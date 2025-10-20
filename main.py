import logging
from threading import Event
from contextlib import suppress

from app.utils.logger_provider import LoggerProvider
from app.config.settings import settings
from concurrency_final.thread_manager import ThreadManager
from concurrency_final.sqs_producer import SQSProducer


def main() -> None:
    LoggerProvider.configure()
    log = logging.getLogger("device-gateway")

    sqs_producer = SQSProducer(
        client_id="sqs-producer-1",
        queue_name=settings.AWS.QUEUE_NAME,
        region=settings.AWS.AWS_REGION,
        endpoint_url=getattr(settings.AWS, "endpoint", None),
        interval_sec=settings.SIM.SEND_INTERVAL_SEC,
        device_ids=list(range(1, settings.SIM.NUM_DEVICES + 1)),
    )
    clients = [sqs_producer]

    mgr = ThreadManager(max_workers=len(clients))
    for c in clients:
        mgr.add_client(c)

    mgr.wait_for_all()

if __name__ == "__main__":
    main()
