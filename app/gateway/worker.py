from __future__ import annotations
import logging
import threading
from typing import Callable, Protocol, Sequence

from botocore.exceptions import BotoCoreError, ClientError

from app.utils.timing import stop_aware_sleep
from app.gateway.sender import send_xml

log = logging.getLogger(__name__)


class SQSProtocol(Protocol):
    def send_message(self, *, QueueUrl: str, MessageBody: str) -> dict: ...


class MessagesWorker:
    """
    Runs on a separate thread: iterates over the devices and sends one message per cycle, until stop_event is set.
    """

    def __init__(
        self,
        *,
        sqs_factory: Callable[[], SQSProtocol],
        queue_url: str,
        device_ids: Sequence[int],
        send_interval_sec: float,
        make_message_xml: Callable[[int], "AnyMessage"],
        initial_delay: float = 0.2,
    ) -> None:
        self._sqs_factory = sqs_factory
        self._queue_url = queue_url
        self._device_ids = list(device_ids)
        self._send_interval_sec = send_interval_sec
        self._make_message_xml = make_message_xml
        self._initial_delay = initial_delay

    def run(self, stop_event: threading.Event) -> None:
        sqs = self._sqs_factory()
        log.info(
            "Messages worker started; queue=%s, devices=%s, interval=%ss",
            self._queue_url,
            self._device_ids,
            self._send_interval_sec,
        )

        stop_aware_sleep(self._initial_delay, stop_event)

        while not stop_event.is_set():
            for device_id in self._device_ids:
                if stop_event.is_set():
                    break
                try:
                    msg = self._make_message_xml(device_id=device_id)
                    provider_id = send_xml(sqs, self._queue_url, msg.payload)
                    log.info("Sent XML from device_id=%s (provider_id=%s)", device_id, provider_id)
                except (ClientError, BotoCoreError) as e:
                    log.error("Failed to send for device_id=%s: %s", device_id, e)

            stop_aware_sleep(self._send_interval_sec, stop_event)

        log.info("Messages worker stopping.")
