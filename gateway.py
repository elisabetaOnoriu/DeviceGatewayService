from __future__ import annotations
import logging
import signal
import threading
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.config.settings import settings
from app.utils.message_factory import make_random_message_xml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
)
log = logging.getLogger("device-gateway")

def make_sqs_client():
    return boto3.client(
        "sqs",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        endpoint_url=settings.endpoint,
    )

def resolve_queue_url(sqs) -> str:
    try:
        return sqs.get_queue_url(QueueName=settings.QUEUE_NAME)["QueueUrl"]
    except (ClientError, BotoCoreError):
        return f"{settings.endpoint.rstrip('/')}/{settings.ACCOUNT_ID}/{settings.QUEUE_NAME}"

def send_xml(sqs, queue_url: str, xml_str: str) -> str:
    resp = sqs.send_message(QueueUrl=queue_url, MessageBody=xml_str)
    return resp.get("MessageId", "")

def stop_aware_sleep(seconds: float, stop_event: threading.Event, step: float = 0.1):
    remaining = seconds
    while remaining > 0 and not stop_event.is_set():
        chunk = min(step, remaining)
        time.sleep(chunk)
        remaining -= chunk

def messages_worker(queue_url: str, stop_event: threading.Event):
    #Runs on a separate thread: iterates over the devices and sends one message per interval.
    sqs = make_sqs_client()
    device_ids = list(range(1, settings.NUM_DEVICES + 1))
    log.info("Messages worker started; queue=%s, devices=%s", queue_url, device_ids)

    # small initial offset
    stop_aware_sleep(0.2, stop_event)

    while not stop_event.is_set():
        for device_id in device_ids:
            if stop_event.is_set():
                break
            try:
                msg = make_random_message_xml(device_id=device_id)
                provider_id = send_xml(sqs, queue_url, msg.payload)
                log.info("Sent XML from device_id=%s (provider_id=%s)", device_id, provider_id)
            except (ClientError, BotoCoreError) as e:
                log.error("Failed to send for device_id=%s: %s", device_id, e)
        # pause between cycles
        stop_aware_sleep(settings.SEND_INTERVAL_SEC, stop_event)

    log.info("Messages worker stopping.")

# ---- Main thread ----
def main():
    log.info(
        "Starting Device Gateway | region=%s endpoint=%s queue=%s devices=%d interval=%ss",
        settings.AWS_REGION, settings.endpoint, settings.QUEUE_NAME,
        settings.NUM_DEVICES, settings.SEND_INTERVAL_SEC
    )

    sqs_boot = make_sqs_client()
    queue_url = resolve_queue_url(sqs_boot)
    log.info("Using queue URL: %s", queue_url)

    stop_event = threading.Event()

    # OS signals → when you press Ctrl+C we want a clean shutdown
    def _signal_handler(signum, frame):
        log.info("Signal %s received → shutting down ...", signum)
        stop_event.set()
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Here we create another thread for messages
    worker = threading.Thread(
        target=messages_worker,
        name="messages-thread",
        args=(queue_url, stop_event),
        daemon=False,
    )
    worker.start()

    # the main thread stays alive and waits for shutdown
    try:
        while not stop_event.is_set():
            time.sleep(0.2)
    finally:
        log.info("Joining messages-thread ...")
        worker.join(timeout=5.0)
        log.info("Shutdown complete.")

if __name__ == "__main__":
    main()