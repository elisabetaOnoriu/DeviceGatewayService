import logging
from concurrency import ThreadManager, SQSProducerClient, SQSConsumerClient
from app.infrastructure.redis_client import RedisClient
from app.config.settings import settings
from app.utils.logger_provider import LoggerProvider

def main() -> None:
    LoggerProvider.configure()
    log = logging.getLogger("device-gateway")

    tm = ThreadManager(log, max_workers=2); tm.start()
    redis = RedisClient(log).get()

    producer = SQSProducerClient(log, settings)
    consumer = SQSConsumerClient(log, settings, redis, worker_threads=4)

    tm.run(producer.run)    
    tm.run(consumer.run)

    while True:
        pass


if __name__ == "__main__":
    main()
