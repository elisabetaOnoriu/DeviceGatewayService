from __future__ import annotations
import json
from typing import Optional, Callable
from .base_worker import BaseWorker

class KafkaConsumerWorker(BaseWorker):
    NAME = "Kafka Consumer"

    def __init__(self, client_id: str, *, topic: str = "device-messages",
                 bootstrap_servers: str = "localhost:9092",
                 group_id: str = "device-gateway",
                 handler: Optional[Callable[[dict], None]] = None) -> None:
        super().__init__(client_id)
        self.topic, self.bootstrap, self.group_id, self.handler = topic, bootstrap_servers, group_id, handler
        self.consumer = None


    def run(self) -> None:
        from kafka import KafkaConsumer
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=[self.bootstrap],
            group_id=self.group_id,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        print(f"[{self.NAME} {self.client_id}] started on {self.thread.name}")
        try:
            for record in self.consumer:
                msg = record.value
                print(f"[{self.NAME} {self.client_id}] received {msg}")
                if self.handler:
                    try: self.handler(msg)
                    except Exception as e: print(f"[{self.NAME} {self.client_id}] handler error: {e}")
                if not self.running.is_set():
                    break
        finally:
            try: self.consumer.close()
            except Exception: pass
            print(f"[{self.NAME} {self.client_id}] Stopped gracefully.")
        
    @classmethod
    def from_settings(cls, settings, client_id: str = "kafka-consumer-1", handler: Optional[Callable[[dict], None]] = None):
        t = getattr(getattr(settings, "KAFKA", object()), "TOPIC", "device-messages")
        b = getattr(getattr(settings, "KAFKA", object()), "BOOTSTRAP", "localhost:9092")
        g = getattr(getattr(settings, "KAFKA", object()), "GROUP", "device-gateway")
        return cls(client_id, topic=t, bootstrap_servers=b, group_id=g, handler=handler)
