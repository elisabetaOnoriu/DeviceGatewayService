from __future__ import annotations
import json, random
import boto3
from botocore.config import Config
from concurrency.base_worker import BaseWorker

class SQSProducerClient(BaseWorker):
    NAME = "SQS Producer"

    def __init__(self, log, settings):
        super().__init__(log, settings)
        self.queue_name = settings.AWS.QUEUE_NAME
        self.interval = settings.SIM.SEND_INTERVAL_SEC
        self.device_ids = list(range(1, settings.SIM.NUM_DEVICES + 1))
        self.sqs = boto3.client(
            "sqs",
            region_name=settings.AWS.AWS_REGION,
            endpoint_url=getattr(settings.AWS, "endpoint", None),
            config=Config(retries={"max_attempts": 3, "mode": "standard"}),
        )
        self.queue_url = self.sqs.get_queue_url(QueueName=self.queue_name)["QueueUrl"]

    def perform_iteration(self) -> None:
        device_id = random.choice(self.device_ids)
        payload = {"device_id": device_id, "value": random.random()}
        self.sqs.send_message(QueueUrl=self.queue_url, MessageBody=json.dumps(payload))

    def run(self, stop_event):
        return super().run(stop_event, sleep_sec=self.interval)
