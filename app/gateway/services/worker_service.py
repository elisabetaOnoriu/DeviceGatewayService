from __future__ import annotations
import logging
import threading
from threading import Event

from app.gateway.worker import MessagesWorker
from app.utils.message_factory import make_random_message_xml
from app.gateway.services.sqs_service import SQSService
from app.gateway.services.redis_service import RedisService


class WorkerService:
    """Manages the worker thread lifecycle"""
    
    def __init__(
        self,
        log: logging.Logger,
        sqs_service: SQSService,
        redis_service: RedisService,
        num_devices: int,
        send_interval_sec: float,
    ):
        self.log = log
        self.sqs_service = sqs_service
        self.redis_service = redis_service
        self.num_devices = num_devices
        self.send_interval_sec = send_interval_sec
        
        self.worker: MessagesWorker | None = None
        self.thread: threading.Thread | None = None
    
    def start(self, stop_event: Event) -> None:
        """Initialize and start the worker thread"""
        device_ids = list(range(1, self.num_devices + 1))
        
        self.worker = MessagesWorker(
            sqs_factory=self.sqs_service.get_client_factory(),
            queue_url=self.sqs_service.get_queue_url(),
            device_ids=device_ids,
            send_interval_sec=self.send_interval_sec,
            make_message_xml=make_random_message_xml,
            initial_delay=0.2,
            redis_connection=self.redis_service.get_connection(),
        )
        
        self.thread = threading.Thread(
            target=self.worker.run,
            name="messages-thread",
            args=(stop_event,),
            daemon=False,
        )
        self.thread.start()
    
    def stop(self, timeout: float = 5.0) -> None:
        if self.thread is not None:
            self.thread.join(timeout=timeout)