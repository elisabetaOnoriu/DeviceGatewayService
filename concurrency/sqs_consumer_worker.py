from __future__ import annotations
import json
import boto3
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor
from concurrency.base_worker import BaseWorker

class SQSConsumerClient(BaseWorker):
    NAME = "SQS Consumer"

    def __init__(self, log, settings, redis_conn, worker_threads: int = 4):
        super().__init__(log, settings)
        self.redis = redis_conn
        self.exec = ThreadPoolExecutor(max_workers=worker_threads, thread_name_prefix="sqs-cons")
        self.queue_name = settings.AWS.QUEUE_NAME
        self.sqs = boto3.client(
            "sqs",
            region_name=settings.AWS.AWS_REGION,
            endpoint_url=getattr(settings.AWS, "endpoint", None),
            config=Config(retries={"max_attempts": 3, "mode": "standard"}),
        )
        self.queue_url = self.sqs.get_queue_url(QueueName=self.queue_name)["QueueUrl"]

    def tick(self) -> None:
        # One iteration: long-poll + dispatch to the internal thread pool
        resp = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=10,  # long poll
        )
        for msg in resp.get("Messages", []):
            body = json.loads(msg["Body"])
            self.exec.submit(self._safe_process, body)
            # Early delete: if you need "delete only after processing", move this into _safe_process
            self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=msg["ReceiptHandle"])

    def _safe_process(self, body: dict) -> None:
        try:
            self._process_one(body)
        except Exception as e:  # log and keep the worker alive
            self.log.error("[SQS Consumer] processing failed: %s", e)

    def _process_one(self, body: dict) -> None:
        # Example side-effect: store latest value per device in Redis
        device_id = body.get("device_id")
        val = body.get("value")
        if self.redis:
            self.redis.set(f"device:{device_id}:last_value", val, ex=3600)

    def on_stop(self) -> None:
        # Gracefully stop the internal pool
        self.exec.shutdown(wait=True, cancel_futures=False)
