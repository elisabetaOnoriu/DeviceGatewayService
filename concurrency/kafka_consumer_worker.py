from __future__ import annotations
import json
from typing import TYPE_CHECKING

from concurrency.base_worker import BaseWorker

if TYPE_CHECKING:
    import logging
    from redis import Redis


class KafkaConsumerWorker(BaseWorker):
    
    def __init__(
        self,
        logger: logging.Logger,
        redis_connection: Redis,
        kafka_topic: str = "device-messages",
        consumer_group: str = "device-gateway-group",
    ):
        super().__init__(logger, redis_connection, "Kafka Consumer")
        self.kafka_topic = kafka_topic
        self.consumer_group = consumer_group
        self.consumer = None
    
    def _startup(self) -> None:
        try:
            from kafka import KafkaConsumer

            self.consumer = KafkaConsumer(
                self.kafka_topic,
                bootstrap_servers=["localhost:9092"],
                group_id=self.consumer_group,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
            )
            self.log.info("[%s] Kafka consumer initialized topic=%s group=%s", self.worker_name, self.kafka_topic, self.consumer_group)
        except Exception:
            self.consumer = None
            self.log.warning("[%s] Kafka consumer not available, using noop", self.worker_name)
    
    def process(self, stop_event=None) -> None:
        if self.consumer is None:
            # noop: sleep briefly
            import time

            time.sleep(0.5)
            return

        # kafka-python provides poll() returning dict(topic_partition->records)
        try:
            messages = self.consumer.poll(timeout_ms=1000)
            for tp, records in messages.items():
                for record in records:
                    if stop_event is not None and stop_event.is_set():
                        return
                    self._process_record(record)
                try:
                    self.consumer.commit()
                except Exception:
                    self.log.exception("[%s] Commit failed", self.worker_name)
        except Exception:
            self.log.exception("[%s] Polling failed", self.worker_name)
    
    def _process_record(self, record) -> None:
        device_id = record.value.get("device_id")
        
        self.log.debug(
            "[%s] Processing device=%d offset=%d",
            self.worker_name,
            device_id,
            record.offset,
        )
        
        # Store în Redis
        key = f"kafka:consumer:device:{device_id}:last"
        self.store_in_redis(key, json.dumps(record.value))
    
    def _cleanup(self) -> None:
        """Cleanup Kafka consumer"""
        if self.consumer:
            try:
                self.consumer.close()
                self.log.info("[%s] Kafka consumer closed", self.worker_name)
            except Exception:
                self.log.exception("[%s] Error closing consumer", self.worker_name)
