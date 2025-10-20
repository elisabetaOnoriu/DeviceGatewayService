from __future__ import annotations
import logging
import threading
import hashlib
import time
from typing import Callable, Protocol, Sequence

from botocore.exceptions import BotoCoreError, ClientError

from app.infrastructure import redis_client as redis_infra
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
        make_message_xml: Callable[[int]],
        initial_delay: float = 0.2,
        redis_connection=None,
    ) -> None:
        self.redis_connection = redis_connection or redis_infra.get_redis()
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
        r = self.redis_connection
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
        r = self.redis_connection
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
        r = self.redis_connection
        if r is None:
            return
        try:
            r.set(f"lastmsg:{device_id}", payload, ex=3600)
            r.set(f"hb:{device_id}", int(time.time()), ex=120)
        except Exception as e:
            log.warning("Cache Redis error for device_id=%s: %s", device_id, e)

    def _redis_smoke_test(self) -> None:
        r = self.redis_connection
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

    def _mirror_message(self, payload: str, device_id: int, limit: int = 100, ttl_sec: int = 3600) -> None:
        r = self.redis_connection
        if r is None:
            return
        try:
            key = "mirror:messages:list"
            now = int(time.time())
            self._push_and_trim(r, key, payload, device_id, now, limit)
            self._prune_old_entries(r, key, now, ttl_sec)
        except Exception as e:
            log.warning("Mirror Redis error: %s", e)

    def _push_and_trim(self, r, key: str, payload: str, device_id: int, now: int, limit: int) -> None:
        import json
        entry = json.dumps({
            "ts": now,
            "device_id": device_id,
            "payload": payload
        })

        p = r.pipeline()
        p.lpush(key, entry)
        p.ltrim(key, 0, limit - 1)
        p.execute()

    def _prune_old_entries(self, r, key: str, now: int, ttl_sec: int) -> None:
        import json
        cutoff = now - ttl_sec

        while True:
            last = r.lindex(key, -1)
            if not last:
                return

            try:
                data = json.loads(last)
                ts = int(data.get("ts", now))
            except Exception:
                r.rpop(key)
                continue

            if ts >= cutoff:
                return

            r.rpop(key)

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
                    self._mirror_message(msg.payload, device_id)
                except (ClientError, BotoCoreError) as e:
                    log.error("Failed to send for device_id=%s: %s", device_id, e)

            stop_aware_sleep(self._send_interval_sec, stop_event)

        log.info("Messages worker stopping.")
