from __future__ import annotations
import logging
from app.gateway.services import LoggingService, RedisService
from app.gateway.concurrency import ThreadManager
from app.config.settings import settings

def bootstrap() -> tuple[logging.Logger, RedisService, ThreadManager]:
    LoggingService.configure()
    log = logging.getLogger("device-gateway")
    log.info(
        "Starting Device Gateway | region=%s queue=%s devices=%d interval=%ss",
        settings.AWS.AWS_REGION, settings.AWS.QUEUE_NAME,
        settings.SIM.NUM_DEVICES, settings.SIM.SEND_INTERVAL_SEC,
    )
    redis = RedisService(log); redis.connect()
    tm = ThreadManager(log, max_workers=4); tm.start()
    return log, redis, tm
