from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from app.infrastructure.redis_client import get_redis

if TYPE_CHECKING:
    from redis import Redis


class RedisService:
    """Handles Redis connection management"""
    
    def __init__(self, logger: logging.Logger):
        self.log = logger
        self.connection: Redis | None = None
    
    def connect(self) -> None:
        self.connection = get_redis()
        
        try:
            self.connection.ping()
            self.log.info("Connected to Redis.")
        except Exception as e:
            self.log.warning("Redis not reachable: %s", e)
    
    def get_connection(self) -> Redis:
        if self.connection is None:
            raise RuntimeError("Redis connection not initialized. Call connect() first.")
        return self.connection