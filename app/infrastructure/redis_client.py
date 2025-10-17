from __future__ import annotations
import os
import redis
import logging
from typing import Optional

class RedisClient:

    def __init__(self, logger: Optional[logging.Logger] = None, url: Optional[str] = None):
        self.log = logger
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._conn: Optional[redis.Redis] = None

    def connect(self) -> redis.Redis:
        if self._conn is None:
            self._conn = redis.Redis.from_url(self.url, decode_responses=True)
            try:
                self._conn.ping()
                if self.log: self.log.info("Connected to Redis (%s)", self.url)
            except Exception as e:
                if self.log: self.log.warning("Redis not reachable: %s", e)
        return self._conn

    def get(self) -> redis.Redis:
        return self.connect()
