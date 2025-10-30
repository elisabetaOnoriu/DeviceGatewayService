import json
from typing import Optional
from kafka import KafkaProducer
from app.models.device_message import DeviceMessage
from .base_worker import BaseWorker

class KafkaProducerWorker(BaseWorker):
    NAME = "Kafka Producer"

    def __init__(self, client_id: str, *, topic: str = "device-messages",
                 bootstrap_servers: str = "localhost:9092",
                 device_ids: Optional[list[int]] = None) -> None:
        super().__init__(client_id)
        self.topic = topic
        self.device_ids = device_ids or [1, 2, 3]
        self._idx = 0
        self.producer = KafkaProducer(
            bootstrap_servers=[bootstrap_servers],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    def _next_device_id(self) -> int:
        d = self.device_ids[self._idx]
        self._idx = (self._idx + 1) % len(self.device_ids)
        return d

    def run(self) -> None:
        try:
            msg = DeviceMessage(device_id=self._next_device_id()).to_dict()
            self.producer.send(self.topic, value=msg)
            print(f"[{self.NAME} {self.client_id}] sent {msg} on {self.thread.name}")
        finally:
            self.producer.flush()
            self.producer.close()

    @classmethod
    def from_settings(cls, settings, client_id: str = "kafka-producer-1") -> "KafkaProducerWorker":
        topic = getattr(getattr(settings, "KAFKA", object()), "TOPIC", "device-messages")
        boot  = getattr(getattr(settings, "KAFKA", object()), "BOOTSTRAP", "localhost:9092")
        n     = int(getattr(getattr(settings, "SIM", object()), "NUM_DEVICES", 3))
        return cls(client_id, topic=topic, bootstrap_servers=boot, device_ids=list(range(1, n + 1)))
