from __future__ import annotations
import json
from typing import Optional, Callable
from .base_worker import BaseWorker

class KafkaConsumerWorker(BaseWorker):
    def __init__(
        self,
        client_id: str,
        *,
        topic: str = "device-messages",
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "device-gateway",
        handler: Optional[Callable[[dict], None]] = None,
    ):
        super().__init__(client_id)
        self.topic = topic
        self.bootstrap = bootstrap_servers
        self.group_id = group_id
        self.handler = handler
        from kafka import KafkaConsumer as _KC
        self._KC = _KC
        self.consumer = None

    @classmethod
    def from_settings(
        cls,
        settings,
        client_id: str = "kafka-consumer-1",
        handler: Optional[Callable[[dict], None]] = None,
    ):
        topic = getattr(getattr(settings, "KAFKA", object()), "TOPIC", "device-messages")
        bootstrap = getattr(getattr(settings, "KAFKA", object()), "BOOTSTRAP", "localhost:9092")
        group = getattr(getattr(settings, "KAFKA", object()), "GROUP", "device-gateway")
        return cls(client_id, topic=topic, bootstrap_servers=bootstrap, group_id=group, handler=handler)

    def run(self) -> None:
        self.consumer = self._KC(
            self.topic,
            bootstrap_servers=[self.bootstrap],
            group_id=self.group_id,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        print(f"[KafkaConsumer {self.client_id}] started on {self.thread.name}")
        try:
            while self.running.is_set():
                records = self.consumer.poll(timeout_ms=1000)
                for _, batch in records.items():
                    for rec in batch:
                        msg = rec.value
                        if self.handler:
                            try:
                                self.handler(msg)
                            except Exception as e:
                                print(f"[KafkaConsumer {self.client_id}] handler error: {e}")
                        print(f"[KafkaConsumer {self.client_id}] received {msg}")
        finally:
            try:
                if self.consumer:
                    self.consumer.close()
            except Exception:
                pass
            print(f"[KafkaConsumer {self.client_id}] Stopped gracefully.")