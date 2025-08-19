# gateway.py
from __future__ import annotations
import time
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config.settings import settings
from app.utils.message_factory import make_random_message_xml

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("device-gateway")


# ---------- SQS helpers ----------
def make_sqs_client():
    """Create a boto3 SQS client pointed at LocalStack (or real AWS if configured)."""
    return boto3.client(
        "sqs",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        endpoint_url=settings.endpoint,  # picks SQS_ENDPOINT_URL or LOCALSTACK_ENDPOINT
    )


def resolve_queue_url(sqs) -> str:
    """Resolve the queue URL; fall back to LocalStack's default account ID if needed."""
    try:
        return sqs.get_queue_url(QueueName=settings.QUEUE_NAME)["QueueUrl"]
    except (ClientError, BotoCoreError):
        # Fallback for LocalStack (static account id)
        return f"{settings.endpoint.rstrip('/')}/{settings.ACCOUNT_ID}/{settings.QUEUE_NAME}"


def send_xml(sqs, queue_url: str, xml_str: str) -> str:
    """Send a raw XML string to SQS and return provider message id."""
    resp = sqs.send_message(QueueUrl=queue_url, MessageBody=xml_str)
    return resp.get("MessageId", "")


# ---------- Main loop ----------
def main():
    log.info(
        "Starting Device Gateway | region=%s endpoint=%s queue=%s devices=%d interval=%ss",
        settings.AWS_REGION,
        settings.endpoint,
        settings.QUEUE_NAME,
        settings.NUM_DEVICES,
        settings.SEND_INTERVAL_SEC,
    )

    sqs = make_sqs_client()
    queue_url = resolve_queue_url(sqs)
    log.info("Using queue URL: %s", queue_url)

    # Simulate device ids: 1..N
    device_ids = list(range(1, settings.NUM_DEVICES + 1))

    try:
        while True:
            # One message per device each cycle
            for device_id in device_ids:
                try:
                    msg = make_random_message_xml(device_id=device_id)
                    provider_id = send_xml(sqs, queue_url, msg.payload)
                    log.info("Sent XML from device_id=%s (provider_id=%s)", device_id, provider_id)
                except (ClientError, BotoCoreError) as e:
                    log.error("Failed to send message for device_id=%s: %s", device_id, e)

            time.sleep(settings.SEND_INTERVAL_SEC)
    except KeyboardInterrupt:
        log.info("Shutting down gracefully.")


if __name__ == "__main__":
    main()
