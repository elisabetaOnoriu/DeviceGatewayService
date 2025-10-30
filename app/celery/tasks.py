from __future__ import annotations
import json
from uuid import uuid4
from kafka import KafkaConsumer
import boto3

from app.celery.config import celery_app
from app.config.settings import settings
from concurrency_final.kafka_producer import KafkaProducerWorker

# ------------ SQS ------------

@celery_app.task(name="app.sqs.produce")
def sqs_produce(n: int = 1) -> str:
    q = boto3.client(
        "sqs",
        region_name=settings.AWS.AWS_REGION,
        endpoint_url=getattr(settings.AWS, "endpoint", None),
    )
    url = q.get_queue_url(QueueName=settings.AWS.QUEUE_NAME)["QueueUrl"]

    num_devices = int(getattr(getattr(settings, "SIM", object()), "NUM_DEVICES", 3))
    sent = 0
    for i in range(max(0, n)):
        msg = {
            "id": str(uuid4()),
            "device_id": (i % max(1, num_devices)) + 1,
        }
        q.send_message(QueueUrl=url, MessageBody=json.dumps(msg))
        print(f"[SQSProducer] sent id={msg['id']} device={msg['device_id']}")
        sent += 1
    return f"SQS sent {sent}"

@celery_app.task(name="app.sqs.consume")
def sqs_consume(n: int = 10) -> str:
    q = boto3.client(
        "sqs",
        region_name=settings.AWS.AWS_REGION,
        endpoint_url=getattr(settings.AWS, "endpoint", None),
    )
    url = q.get_queue_url(QueueName=settings.AWS.QUEUE_NAME)["QueueUrl"]

    got = 0
    while got < n:
        remaining = n - got
        resp = q.receive_message(
            QueueUrl=url,
            MaxNumberOfMessages=min(10, remaining),
            WaitTimeSeconds=5,
        )
        for m in resp.get("Messages", []):
            body = json.loads(m["Body"])
            print(f"[SQSConsumer] received id={body.get('id')} device={body.get('device_id')}")
            q.delete_message(QueueUrl=url, ReceiptHandle=m["ReceiptHandle"])
            got += 1
            if got >= n:
                break
        if not resp.get("Messages"):
            break
    return f"SQS consumed {got}"

# ------------ KAFKA ------------

@celery_app.task(name="app.kafka.produce")
def kafka_produce(n: int = 1) -> str:
    worker = KafkaProducerWorker.from_settings(settings, client_id="celery-kafka-producer")
    num_devices = int(getattr(getattr(settings, "SIM", object()), "NUM_DEVICES", 3))

    sent = 0
    for i in range(max(0, n)):
        msg = {
            "id": str(uuid4()),
            "device_id": (i % max(1, num_devices)) + 1,
        }
        worker.producer.send(worker.topic, value=msg)
        print(f"[KafkaProducer] sent id={msg['id']} device={msg['device_id']}")
        sent += 1
    worker.producer.flush()
    worker.producer.close()
    return f"Kafka sent {sent}"

@celery_app.task(name="app.kafka.consume")
def kafka_consume(n: int = 1) -> str:
    consumer = KafkaConsumer(
        "device-messages",
        bootstrap_servers=["localhost:9092"],
        auto_offset_reset="latest",
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    count = 0
    for rec in consumer:
        print(f"[KafkaConsumer] received {rec.value}")
        count += 1
        if count >= n:
            break
    consumer.close()
    return f"Kafka consumed {count}"
