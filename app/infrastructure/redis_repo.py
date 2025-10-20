# app/infra/redis_repo.py
import time
import json
import logging
from typing import Optional

log = logging.getLogger(__name__)

class RedisRepo:
    def __init__(self, redis_client: Optional[object]) -> None:
        self.r = redis_client

    def available(self) -> bool:
        return self.r is not None

    # key/value helpers
    def set(self, key: str, value, *, ex: Optional[int] = None, nx: bool = False):
        if not self.r: return None
        return self.r.set(key, value, ex=ex, nx=nx)

    def get(self, key: str):
        if not self.r: return None
        return self.r.get(key)

    def incr(self, key: str) -> int:
        if not self.r: return 0
        return int(self.r.incr(key))

    def expire(self, key: str, ttl: int) -> None:
        if not self.r: return
        self.r.expire(key, ttl)

    # list helpers (mirror)
    def lpush(self, key: str, value: str) -> None:
        if not self.r: return
        self.r.lpush(key, value)

    def ltrim(self, key: str, start: int, end: int) -> None:
        if not self.r: return
        self.r.ltrim(key, start, end)

    def lindex(self, key: str, idx: int):
        if not self.r: return None
        return self.r.lindex(key, idx)

    def rpop(self, key: str):
        if not self.r: return None
        return self.r.rpop(key)

    def pipeline(self):
        if not self.r:
            class _Noop:
                def lpush(self, *_): return self
                def ltrim(self, *_): return self
                def execute(self): return None
            return _Noop()
        return self.r.pipeline()
