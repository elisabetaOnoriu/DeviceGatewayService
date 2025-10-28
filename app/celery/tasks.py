from __future__ import annotations
import logging
import json

from app.celery.config import celery_app
from app.models.device_message import DeviceMessage
from concurrency_final.kafka_consumer import KafkaConsumerWorker
from concurrency_final.sqs_producer import SQSProducer
from concurrency_final.sqs_consumer import SQSConsumer
from concurrency_final.kafka_producer import KafkaProducerWorker
from app.config.settings import settings

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.process_event")
def process_event(self, msg: dict) -> dict:
    print(f"[task={self.request.id}] {msg}")
    return {"received": msg, "task_id": self.request.id}

@celery_app.task(name="app.sqs.produce")
def send_sqs_messages(n: int = 10, interval_sec: float | None = None) -> str:
    producer = SQSProducer.from_settings(settings, client_id="celery-sqs-producer")

    if interval_sec is not None:
        producer.interval_sec = interval_sec

    for _ in range(n):
        device_id = producer._next_device_id()
        payload = DeviceMessage(device_id=device_id).to_dict()
        body = json.dumps(payload)

        producer.sqs.send_message(QueueUrl=producer.queue_url, MessageBody=body)
        print(f"[SQSProducer {producer.client_id}] sent {body}")

    return f"Sent {n} messages to {producer.queue_url}"

@celery_app.task(name="app.sqs.consume")
def receive_sqs_messages(max_messages: int = 10) -> str:
    consumer = SQSConsumer.from_settings(settings, client_id="celery-sqs-consumer")
    received = 0

    while received < max_messages:
        remaining = max_messages - received
        messages = consumer.sqs.receive_message(
            QueueUrl=consumer.queue_url,
            MaxNumberOfMessages=min(10, remaining),
            WaitTimeSeconds=5,
        ).get("Messages", [])

        if not messages:
            break

        for message in messages[:remaining]:
            body = message["Body"]
            print(f"[SQSConsumer {consumer.client_id}] received {body}")
            consumer.sqs.delete_message(
                QueueUrl=consumer.queue_url,
                ReceiptHandle=message["ReceiptHandle"],
            )
            received += 1

    return f"Received and deleted {received} messages from {consumer.queue_url}"

@celery_app.task(name="app.kafka.produce")
def send_kafka_messages(n: int = 10) -> str:
    producer = KafkaProducerWorker.from_settings(settings, client_id="celery-kafka-producer")

    for _ in range(n):
        device_id = producer.device_ids[producer._idx]
        producer._idx = (producer._idx + 1) % len(producer.device_ids)

        message = DeviceMessage(device_id=device_id).to_dict()
        producer.producer.send(producer.topic, value=message)
        print(f"[KafkaProducer {producer.client_id}] sent {message}")

    producer.producer.flush()
    return f"Sent {n} messages to Kafka topic {producer.topic}"

@celery_app.task(name="app.kafka.consume")
def receive_kafka_messages(n: int = 10) -> str:

    consumer = KafkaConsumerWorker.from_settings(settings, client_id="celery-kafka-consumer")._KC(
        "device-messages",
        bootstrap_servers=["localhost:9092"],
        group_id="device-gateway",
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    count = 0
    for message in consumer:
        print(f"[KafkaConsumer] received {message.value}")
        count += 1
        if count >= n:
            break

    consumer.close()
    return f"Received {count} messages"

