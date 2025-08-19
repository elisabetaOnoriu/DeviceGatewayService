from __future__ import annotations
import os
import time
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.models.message_factory import make_random_message_xml  # produce XML via template

# ---------- Config (env) ----------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
LOCALSTACK_ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
QUEUE_NAME = os.getenv("QUEUE_NAME", "device-messages")
SEND_INTERVAL_SEC = int(os.getenv("SEND_INTERVAL_SEC", "2"))

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("device-gateway")

# ---------- SQS ----------
def sqs_client():
    return boto3.client(
        "sqs",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        endpoint_url=LOCALSTACK_ENDPOINT,
    )

def resolve_queue_url(sqs):
    """Prefer AWS API; fall back to LocalStack implicit URL."""
    try:
        resp = sqs.get_queue_url(QueueName=QUEUE_NAME)
        return resp["QueueUrl"]
    except (ClientError, BotoCoreError):
        # LocalStack default account id
        return f"{LOCALSTACK_ENDPOINT.rstrip('/')}/000000000000/{QUEUE_NAME}"

def send_xml(xml_str: str) -> str:
    sqs = sqs_client()
    queue_url = resolve_queue_url(sqs)
    resp = sqs.send_message(QueueUrl=queue_url, MessageBody=xml_str)
    return resp.get("MessageId", "")

# ---------- Main loop ----------
def main():
    log.info(
        "Starting Device Gateway → region=%s endpoint=%s queue=%s interval=%ss",
        AWS_REGION, LOCALSTACK_ENDPOINT, QUEUE_NAME, SEND_INTERVAL_SEC,
    )
    try:
        while True:
            msg = make_random_message_xml()   # MessageCreate (payload = XML string)
            message_id = send_xml(msg.payload)
            log.info("Sent message to SQS (provider_id=%s)", message_id)
            time.sleep(SEND_INTERVAL_SEC)
    except KeyboardInterrupt:
        log.info("Shutting down gracefully.")

if __name__ == "__main__":
    main()
