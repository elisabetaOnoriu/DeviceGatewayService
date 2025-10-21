from __future__ import annotations
import json
import time
from typing import Optional

from .base_worker import BaseWorker

class KafkaProducerWorker(BaseWorker):
    def __init__(
        self,
        client_id: str,
        *,
        topic: str = "device-messages",
        bootstrap_servers: str = "localhost:9092",
        interval_sec: float = 1.0,
        device_ids: Optional[list[int]] = None,
        redis=None,  # opțional
    ) -> None:
        super().__init__(client_id)
        self.topic = topic
        self.interval_sec = interval_sec
        self.device_ids = device_ids or [1, 2, 3]
        self.redis = redis
        self._idx = 0  # round-robin

        from kafka import KafkaProducer as _KafkaProducer
        self.producer = _KafkaProducer(
            bootstrap_servers=[bootstrap_servers],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    def run(self) -> None:
        try:
            while self.running.is_set():
                # pick device id round-robin
                device_id = self.device_ids[self._idx]
                self._idx = (self._idx + 1) % len(self.device_ids)

                message = {
                    "device_id": device_id,
                    "timestamp": time.time(),
                    "data": {
                        "temperature": 20 + (device_id % 10),
                        "humidity": 50 + (device_id % 20),
                    },
                }

                try:
                    self.producer.send(self.topic, value=message)
                    print(f"[KafkaProducer {self.client_id}] sent {message} on {self.thread.name}")
                except Exception as e:
                    print(f"[KafkaProducer {self.client_id}] send failed: {e}")
                    self.running.clear()
                    break

            
                time.sleep(self.interval_sec)
        finally:
            try:
                self.producer.flush()
                self.producer.close()
                print(f"[KafkaProducer {self.client_id}] closed")
            except Exception as e:
                print(f"[KafkaProducer {self.client_id}] close failed: {e}")

        print(f"[KafkaProducer {self.client_id}] Stopped gracefully.")

    @classmethod
    def from_settings(cls, settings, client_id: str = "kafka-producer-1", *, redis=None):
        return cls(
            client_id=client_id,
            topic=getattr(getattr(settings, "KAFKA", object()), "TOPIC", "device-messages"),
            bootstrap_servers=getattr(getattr(settings, "KAFKA", object()), "BOOTSTRAP", "localhost:9092"),
            interval_sec=getattr(getattr(settings, "SIM", object()), "SEND_INTERVAL_SEC", 1.0),
            device_ids=list(range(1, int(getattr(getattr(settings, "SIM", object()), "NUM_DEVICES", 3)) + 1)),
            redis=redis,
        )