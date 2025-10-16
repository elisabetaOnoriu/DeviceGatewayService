from __future__ import annotations
import logging, time
from services.logging_service import LoggingService
from services.redis_service import RedisService
from concurrency.thread_manager import ThreadManager
from concurrency.sqs_producer_worker import SQSProducerClient
from concurrency.sqs_consumer_worker import SQSConsumerClient
from app.config.settings import settings

def main() -> None:
    LoggingService.configure()
    log = logging.getLogger("device-gateway")

    tm = ThreadManager(log, max_workers=2); tm.start()
    redis = RedisService(log); redis.connect()

    producer = SQSProducerClient(log, settings)
    consumer = SQSConsumerClient(log, settings, redis.get_connection(), worker_threads=4)

    tm.run(producer.run)    
    tm.run(consumer.run)

    try:
        while True: time.sleep(0.5)
    except KeyboardInterrupt:
        log.info("Shutting down..."); tm.stop(timeout=10)

if __name__ == "__main__":
    main()
