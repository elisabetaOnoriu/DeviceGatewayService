from __future__ import annotations
import json
import boto3
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor
from concurrency_final.base_worker import BaseWorker
import threading

class SQSConsumer(BaseWorker):
    NAME = "SQS Consumer"

    def __init__(self, log, settings, redis_conn, worker_threads: int = 4):
        super().__init__(log, settings)
        self.redis = redis_conn
        self.exec = ThreadPoolExecutor(max_workers=worker_threads, thread_name_prefix="sqs-cons")
        self.sqs = boto3.client(
            "sqs",
            region_name=settings.AWS.AWS_REGION,
            endpoint_url=getattr(settings.AWS, "endpoint", None),
            config=Config(retries={"max_attempts": 3, "mode": "standard"}),
        )
        self.queue_url = self.sqs.get_queue_url(QueueName=settings.AWS.QUEUE_NAME)["QueueUrl"]


    def run(self) -> None:
        try:
            while self.running.is_set():
                resp = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=4,
                    WaitTimeSeconds=10,
                )
                for msg in resp.get("Messages", []):
                    self.exec.submit(self._process_then_ack, msg["Body"], msg["ReceiptHandle"])
        finally:
            self.exec.shutdown(wait=True, cancel_futures=False)

    def _process_then_ack(self, raw_body: str, receipt: str) -> None:
        try:
            payload = json.loads(raw_body)
            self._process_one(payload)         
            print(f"[SQS Consumer] RECEIVED message body={payload} on {threading.current_thread().name}")
            self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt)
        except Exception as e:
            self.log.error("[SQS Consumer] processing failed: %s", e)

    def _process_one(self, body: dict) -> None:
        device_id = body.get("device_id")
        if self.redis and device_id is not None:
            self.redis.set(f"device:{device_id}:last_value", body.get("value"), ex=3600)

    @classmethod
    def from_settings(cls, log, settings, redis_conn, worker_threads: int = 4):
        return cls(
            log=log,
            settings=settings,
            redis_conn=redis_conn,
            worker_threads=worker_threads,
        )