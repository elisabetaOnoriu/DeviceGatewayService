from __future__ import annotations
import json, threading
import boto3
from botocore.config import Config
from concurrency_final.base_worker import BaseWorker

class SQSConsumer(BaseWorker):
    NAME = "SQS Consumer"

    def __init__(self, client_id: str, settings, redis_conn=None, handler=None):
        super().__init__(client_id)
        self.redis = redis_conn
        self.handler = handler
        self.sqs = boto3.client(
            "sqs",
            region_name=settings.AWS.AWS_REGION,
            endpoint_url=getattr(settings.AWS, "endpoint", None),
            config=Config(retries={"max_attempts": 3, "mode": "standard"}),
        )
        self.queue_url = self.sqs.get_queue_url(QueueName=settings.AWS.QUEUE_NAME)["QueueUrl"]


    def run(self) -> None:
        try:
            resp = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=4,
                WaitTimeSeconds=10,
            )
            for msg in resp.get("Messages", []) or []:
                self._process_then_ack(msg["Body"], msg["ReceiptHandle"])
        finally:
            pass

    def _process_then_ack(self, raw_body: str, receipt: str) -> None:
        try:
            payload = json.loads(raw_body)
            self._process_one(payload)
            if self.handler:
                try:
                    self.handler(payload)
                except Exception as e:
                    print(f"[SQS Consumer {self.client_id}] handler error: {e}")
            print(f"[SQS Consumer {self.client_id}] RECEIVED body={payload} on {threading.current_thread().name}")
            self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt)
        except Exception as e:
            print(f"[SQS Consumer {self.client_id}] processing failed: {e}")

    def _process_one(self, body: dict) -> None:
        device_id = body.get("device_id")
        if self.redis and device_id is not None:
            self.redis.set(f"sqs:consumer:device:{device_id}:last", json.dumps(body), ex=3600)

    @classmethod
    def from_settings(cls, settings, redis_conn=None, client_id: str = "sqs-consumer-1", handler=None):
        return cls(
            client_id=client_id,
            settings=settings,
            redis_conn=redis_conn,
            handler=handler,
        )
