from __future__ import annotations
import time
import json
from typing import TYPE_CHECKING

from app.gateway.concurrency.base_worker import BaseWorker

if TYPE_CHECKING:
    import logging
    from redis import Redis


class KafkaProducerWorker(BaseWorker):
    
    def __init__(
        self,
        logger: logging.Logger,
        device_ids: list[int],
        send_interval_sec: float,
        redis_connection: Redis,
        kafka_topic: str = "device-messages",
    ):
        super().__init__(logger, redis_connection, "Kafka Producer")
        self.device_ids = device_ids
        self.send_interval_sec = send_interval_sec
        self.kafka_topic = kafka_topic
        self.producer = None
    
    def _startup(self) -> None:
        try:
            from kafka import KafkaProducer

            self.producer = KafkaProducer(
                bootstrap_servers=["localhost:9092"],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            self.log.info("[%s] Kafka producer initialized for topic %s", self.worker_name, self.kafka_topic)
        except Exception:
            self.producer = None
            self.log.warning("[%s] Kafka producer not available, using noop", self.worker_name)
    
    def process(self, stop_event=None) -> None:
        for device_id in self.device_ids:
            if stop_event is not None and stop_event.is_set():
                return
            try:
                message = {
                    "device_id": device_id,
                    "timestamp": time.time(),
                    "data": {
                        "temperature": 20 + (device_id % 10),
                        "humidity": 50 + (device_id % 20),
                    },
                }

                # Send to Kafka (if available)
                if self.producer:
                    try:
                        self.producer.send(self.kafka_topic, value=message)
                    except Exception:
                        self.log.exception("[%s] Kafka send failed for device=%d", self.worker_name, device_id)
                else:
                    self.log.debug("[%s] (noop) would send: %s", self.worker_name, message)

                self.log.debug("[%s] Sent device=%d", self.worker_name, device_id)

                # Store în Redis
                key = f"kafka:producer:device:{device_id}:last"
                self.store_in_redis(key, json.dumps(message))

            except Exception as e:
                self.log.error("[%s] Failed device=%d: %s", self.worker_name, device_id, e)

        # Sleep in small increments so we can respond to shutdown quickly
        remaining = self.send_interval_sec
        step = 0.1
        while remaining > 0:
            if stop_event is not None and stop_event.is_set():
                return
            time.sleep(min(step, remaining))
            remaining -= step
    
    def _cleanup(self) -> None:
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
                self.log.info("[%s] Kafka producer closed", self.worker_name)
            except Exception:
                self.log.exception("[%s] Error closing producer", self.worker_name)