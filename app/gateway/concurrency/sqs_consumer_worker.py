"""SQS Consumer Worker - Citește mesaje din SQS"""
from __future__ import annotations
import time
from typing import TYPE_CHECKING

from app.gateway.concurrency.base_worker import BaseWorker
from app.gateway.sqs import make_sqs_client, resolve_queue_url

if TYPE_CHECKING:
    import logging
    from redis import Redis


class SQSConsumerWorker(BaseWorker):
    
    def __init__(
        self,
        logger: logging.Logger,
        redis_connection: Redis,
        poll_interval_sec: float = 1.0,
        max_messages: int = 10,
    ):
        super().__init__(logger, redis_connection, "SQS Consumer")
        self.poll_interval_sec = poll_interval_sec
        self.max_messages = max_messages
        self.sqs_client = None
        self.queue_url = None
    
    def _startup(self) -> None:
        self.sqs_client = make_sqs_client()
        self.queue_url = resolve_queue_url(self.sqs_client)
        self.log.info("[%s] Queue URL: %s", self.worker_name, self.queue_url)
    
    def process(self) -> None:
        response = self.sqs_client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=self.max_messages,
            WaitTimeSeconds=5,
        )
        
        messages = response.get("Messages", [])
        
        if messages:
            self.log.info("[%s] Received %d messages", self.worker_name, len(messages))
            
            for message in messages:
                self._process_message(message)
        
        time.sleep(self.poll_interval_sec)
    
    def _process_message(self, message: dict) -> None:
        """Processes individual message"""
        message_id = message.get("MessageId")
        body = message.get("Body")
        receipt_handle = message.get("ReceiptHandle")
        
        self.log.debug("[%s] Processing MessageId=%s", self.worker_name, message_id)
        
        # Store în Redis
        key = f"sqs:consumer:processed:{message_id}"
        self.store_in_redis(key, body)
        
        # Delete from queue
        self.sqs_client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle,
        )