from kafka import KafkaProducer
import json, time, random

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)
print("Starting producer...")
for i in range(10):  # send 10 messages
    event = {"id": i, "value": random.random()}
    producer.send("test-topic", event)
    print("Produced:", event)
    time.sleep(1)

producer.flush()
print("Done producing.")