from __future__ import annotations
import logging
import threading
import hashlib
import time
from typing import Callable, Protocol, Sequence

from botocore.exceptions import BotoCoreError, ClientError

from app.infrastructure import redis_client
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
        redis_client=None,
    ) -> None:
        self.redis_client = redis_client
        self._sqs_factory = sqs_factory
        self._queue_url = queue_url
        self._device_ids = list(device_ids)
        self._send_interval_sec = send_interval_sec
        self._make_message_xml = make_message_xml
        self._initial_delay = initial_delay


    def _rate_limit_ok(self, device_id: int, limit: int = 30, window_sec: int = 60) -> bool:
        """
        Fixed-window: allows at most `limit` messages per `window_sec` for a device.
        Uses INCR + EXPIRE. If Redis is absent/unavailable, allows (fail-open).
        """
        r = self.redis_client
        if r is None:
            return True
        try:
            key = f"rate:{device_id}:{int(time.time() // window_sec)}"
            cnt = r.incr(key)
            if cnt == 1:
                r.expire(key, window_sec)
            return cnt <= limit
        except Exception as e:
            log.warning("RateLimit Redis error for device_id=%s: %s", device_id, e)
            return True  # fail-open

    def _is_duplicate(self, payload: str, ttl_sec: int = 3600) -> bool:
        """
        Idempotency: returns True if the payload was seen in the last `ttl_sec` seconds.
        Uses MD5(payload) and SET NX with TTL.
        """
        r = self.redis_client
        if r is None:
            return False
        try:
            msg_id = hashlib.md5(payload.encode()).hexdigest()
            ok = r.set(f"msg:{msg_id}", "1", ex=ttl_sec, nx=True)
            return not bool(ok)  # if not set => existed => duplicate
        except Exception as e:
            log.warning("Idempotency Redis error: %s", e)
            return False

    def _cache_last_and_heartbeat(self, device_id: int, payload: str) -> None:
        """
        Stores the last message and a short heartbeat with TTL.
        """
        r = self.redis_client
        if r is None:
            return
        try:
            r.set(f"lastmsg:{device_id}", payload, ex=3600)
            r.set(f"hb:{device_id}", int(time.time()), ex=120)
        except Exception as e:
            log.warning("Cache Redis error for device_id=%s: %s", device_id, e)

    def _redis_smoke_test(self) -> None:
        r = self.redis_client
        if r is None:
            log.info("Redis client is None — skipping Redis smoke test.")
            return
        try:
            name = "hello"
            r.set("greeting", name, ex=60)
            val = r.get("greeting")
            if isinstance(val, bytes):
                val = val.decode("utf-8", errors="ignore")
            log.info("Redis smoke test OK: greeting=%r", val)
        except Exception as e:
            log.warning("Redis smoke test FAILED: %s", e)

    def run(self, stop_event: threading.Event) -> None:
        sqs = self._sqs_factory()
        log.info(
            "Messages worker started; queue=%s, devices=%s, interval=%ss",
            self._queue_url,
            self._device_ids,
            self._send_interval_sec,
        )

        self._redis_smoke_test()

        stop_aware_sleep(self._initial_delay, stop_event)

        while not stop_event.is_set():
            for device_id in self._device_ids:
                if stop_event.is_set():
                    break
                try:
                    msg = self._make_message_xml(device_id=device_id)

                    # (1) Rate limit
                    if not self._rate_limit_ok(device_id):
                        log.debug("Rate limited device_id=%s", device_id)
                        continue

                    # (2) Idempotency / dedup
                    if self._is_duplicate(msg.payload):
                        log.debug("Duplicate skipped for device_id=%s", device_id)
                        continue

                    # (3) Send + cache/heartbeat
                    provider_id = send_xml(sqs, self._queue_url, msg.payload)
                    log.info("Sent XML from device_id=%s (provider_id=%s)", device_id, provider_id)
                    self._cache_last_and_heartbeat(device_id, msg.payload)
                except (ClientError, BotoCoreError) as e:
                    log.error("Failed to send for device_id=%s: %s", device_id, e)

            stop_aware_sleep(self._send_interval_sec, stop_event)

        log.info("Messages worker stopping.")
