import os
from celery import Celery

BROKER  = os.getenv("CELERY_BROKER_URL",   "redis://localhost:6379/0")
BACKEND = os.getenv("CELERY_RESULT_BACKEND","redis://localhost:6379/1")


celery_app = Celery("tasks", broker=BROKER, backend=BACKEND)
celery_app.conf.update(
    include=["app.celery.tasks"],
    broker_connection_retry_on_startup = True,
)


celery_app.conf.beat_schedule = {
    "send-sqs-m-every-1.5s": {
        "task": "app.sqs.produce",
        "schedule": 1.5,
        "args": (1, 1.5),
    },
    "receive-sqs-m-every-1.5s": {
        "task": "app.sqs.consume",
        "schedule": 1.5,
        "args": (1,),
    },
    "kafka-produce-every-2s": {
        "task": "app.kafka.produce",
        "schedule": 2.0,
        "kwargs": {"n": 1},
    },
    "kafka-consume-every-2s": {
        "task": "app.kafka.consume",
        "schedule": 2.0,
        "kwargs": {"n": 1},
    },
}