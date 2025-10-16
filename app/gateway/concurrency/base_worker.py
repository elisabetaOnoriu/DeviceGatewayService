from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from threading import Event
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redis import Redis


class BaseWorker(ABC):

    def __init__(self, logger: logging.Logger, redis_connection: Redis, worker_name: str):
        self.log = logger
        self.redis = redis_connection
        self.name = worker_name
        # Backwards-compatible aliases
        self.worker_name = self.name
        self.redis_connection = self.redis

    def run(self, stop_event: Event) -> None:
        self.log.info("[%s] Starting...", self.name)
        try:
            while not stop_event.is_set():
                try:
                    try:
                        self.process(stop_event)
                    except TypeError:
                        self.process()
                except Exception:
                    self.log.exception("[%s] Process error", self.name)
        except Exception:
            self.log.exception("[%s] Fatal error", self.name)
        finally:
            self.log.info("[%s] Stopped", self.name)

    @abstractmethod
    def process(self, stop_event: Event | None = None) -> None:
        """Do one unit of work. Implementors may accept stop_event to react to shutdown."""
        raise NotImplementedError()

    def store_in_redis(self, key: str, value: str, ttl: int = 3600) -> None:
        try:
            self.redis.setex(key, ttl, value)
        except Exception:
            self.log.exception("[%s] Redis store failed", self.name)

    def get_from_redis(self, key: str) -> str | None:
        try:
            v = self.redis.get(key)
            return v.decode("utf-8") if v else None
        except Exception:
            self.log.exception("[%s] Redis get failed", self.name)
            return None