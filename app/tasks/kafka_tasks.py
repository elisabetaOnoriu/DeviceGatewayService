import os, json, time, random
from kafka import KafkaProducer
from app.config.celery_app import celery_app

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")  # or localhost:29092

@celery_app.task(name="app.tasks.send_kafka_events")
def send_kafka_events(n=10, topic="test-topic", delay_sec=1.0):
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    for i in range(n):
        event = {"id": i, "value": random.random()}
        producer.send(topic, event)
        time.sleep(delay_sec)
    producer.flush()
    return f"Sent {n} events to {topic}"
