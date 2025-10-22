import threading
import time
import json
from uuid import uuid4
import boto3

from app.models.device_message import DeviceMessage
from .base_worker import BaseWorker

class SQSProducer(BaseWorker):
    def __init__(
        self,
        client_id: str,
        queue_name: str,
        *,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
        interval_sec: float = 1.0,
        device_ids: list[int] | None = None,
    ):
        super().__init__(client_id)
        self.interval_sec = interval_sec
        self.device_ids = device_ids or [1, 2, 3]
        self._idx = 0

        self.sqs = boto3.client("sqs", region_name=region, endpoint_url=endpoint_url)
        self.queue_url = self.sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]

    def _next_device_id(self) -> int:
        d = self.device_ids[self._idx]
        self._idx = (self._idx + 1) % len(self.device_ids)
        return d

    def run(self):
        while self.running.is_set():
            device_id = self._next_device_id()
            payload = DeviceMessage.create_for_device(device_id).to_dict()
            body = json.dumps(payload)

            try:
                self.sqs.send_message(QueueUrl=self.queue_url, MessageBody=body)
                print(f"[SQSProducer {self.client_id}] sent {body} on {self.thread.name}")
                time.sleep(self.interval_sec)
            except Exception as e:
                print(f"[SQSProducer {self.client_id}] send failed: {e}")
                self.running.clear()

        print(f"[SQSProducer {self.client_id}] Stopped gracefully.")

    @classmethod
    def from_settings(cls, settings, client_id: str = "sqs-producer-1"):
        return cls(
            client_id=client_id,
            queue_name=settings.AWS.QUEUE_NAME,
            region=settings.AWS.AWS_REGION,
            endpoint_url=getattr(settings.AWS, "endpoint", None),
            interval_sec=settings.SIM.SEND_INTERVAL_SEC,
            device_ids=list(range(1, settings.SIM.NUM_DEVICES + 1)),
        )
