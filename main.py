import logging
import time
from app.celery.tasks import send_sqs_messages
from app.infrastructure.redis_client import RedisClient
from app.utils.logger_provider import LoggerProvider
from app.config.settings import settings
from app.celery.start import spawn


def main() -> None:
    LoggerProvider.configure()
    log = logging.getLogger("device-gateway")

    #redis_connection = RedisClient(log).get()

    # sqs_producer = SQSProducer.from_settings(settings)
    # sqs_consumer = SQSConsumer.from_settings(settings, redis_connection, worker_threads=4)
    # kafka_producer = KafkaProducerWorker.from_settings(settings, client_id="kafka-producer-1", redis=redis_connection)
    # kafka_consumer = KafkaConsumerWorker.from_settings(settings, client_id="kafka-consumer-1")
    
    # clients = [sqs_producer, sqs_consumer, kafka_producer, kafka_consumer]
    # manager = ThreadManager(max_workers=len(clients))
    
    # for c in clients:
    #     manager.add_client(c)

    # manager.wait_for_all()
    workers = ["sqs_producer", "sqs_consumer", "kafka_producer", "kafka_consumer"]

    processes = [
        spawn("worker", f"-n {name}@%h --concurrency=1")
        for name in workers
    ]
    processes.append(spawn("beat"))

    for p in processes:
        p.wait()

  

if __name__ == "__main__":
    main()
