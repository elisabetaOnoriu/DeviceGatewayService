# app/infra/redis_client.py
import os
import redis

_redis = None

def get_redis():
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis = redis.Redis.from_url(url, decode_responses=True)
    return _redis
