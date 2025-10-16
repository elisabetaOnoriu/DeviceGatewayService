from __future__ import annotations
import time
from typing import TYPE_CHECKING

from app.gateway.concurrency.base_worker import BaseWorker
from app.gateway.sqs import make_sqs_client, resolve_queue_url
from app.utils.message_factory import make_random_message_xml

if TYPE_CHECKING:
    import logging
    from redis import Redis


class SQSProducerWorker(BaseWorker):
    """Producer pentru SQS - extinde BaseWorker"""
    
    def __init__(
        self,
        logger: logging.Logger,
        device_ids: list[int],
        send_interval_sec: float,
        redis_connection: Redis,
    ):
        super().__init__(logger, redis_connection, "SQS Producer")
        self.device_ids = device_ids
        self.send_interval_sec = send_interval_sec
        self.sqs_client = None
        self.queue_url = None
    
    def _startup(self) -> None:
        self.sqs_client = make_sqs_client()
        self.queue_url = resolve_queue_url(self.sqs_client)
        self.log.info("[%s] Queue URL: %s", self.worker_name, self.queue_url)
    
    def process(self) -> None:
        """Procesare: trimite batch de mesaje"""
        for device_id in self.device_ids:
            try:
                message_xml = make_random_message_xml(device_id)
                
                response = self.sqs_client.send_message(
                    QueueUrl=self.queue_url,
                    MessageBody=message_xml,
                )
                
                message_id = response.get("MessageId")
                self.log.debug(
                    "[%s] Sent device=%d MessageId=%s",
                    self.worker_name,
                    device_id,
                    message_id,
                )
                
                key = f"sqs:producer:device:{device_id}:last"
                self.store_in_redis(key, f"{message_id}:{time.time()}")
                
            except Exception as e:
                self.log.error(
                    "[%s] Failed device=%d: %s",
                    self.worker_name,
                    device_id,
                    e,
                )
        
        time.sleep(self.send_interval_sec)