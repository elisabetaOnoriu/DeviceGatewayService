from __future__ import annotations
import logging
import threading
import time

from app.config.settings import settings
from app.utils.shutdown import ShutdownHandler
from app.utils.message_factory import make_random_message_xml

from app.gateway.sqs import make_sqs_client, resolve_queue_url
from app.gateway.worker import MessagesWorker


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
    )


def main() -> None:
    configure_logging()
    log = logging.getLogger("device-gateway")

    log.info(
        "Starting Device Gateway | region=%s endpoint=%s queue=%s devices=%d interval=%ss",
        settings.AWS.REGION,           # <- nested
        settings.AWS.endpoint,         # <- property în AwsSettings
        settings.AWS.QUEUE_NAME,       # <- nested
        settings.SIM.NUM_DEVICES,      # <- din SimulationSettings
        settings.SIM.SEND_INTERVAL_SEC # <- din SimulationSettings
    )

    """bootstrap SQS + queue URL"""
    sqs_boot = make_sqs_client()
    queue_url = resolve_queue_url(sqs_boot)
    log.info("Using queue URL: %s", queue_url)

    """prepare worker"""
    device_ids = list(range(1, settings.SIM.NUM_DEVICES + 1))
    worker = MessagesWorker(
        sqs_factory=make_sqs_client,
        queue_url=queue_url,
        device_ids=device_ids,
        send_interval_sec=settings.SIM.SEND_INTERVAL_SEC,
        make_message_xml=make_random_message_xml,
        initial_delay=0.2,
    )

    shutdown = ShutdownHandler(log)
    stop_event = shutdown.stop_event

    thread = threading.Thread(
        target=worker.run,
        name="messages-thread",
        args=(stop_event,),
        daemon=False,
    )
    thread.start()

    try:
        """main thread idling until the shutdown signal (Ctrl+C / OS signals)"""
        while not stop_event.is_set():
            time.sleep(0.2)
    finally:
        log.info("Joining messages-thread ...")
        thread.join(timeout=5.0)
        log.info("Shutdown complete.")


if __name__ == "__main__":
    main()
