import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("device_gateway", broker=REDIS_URL)

celery_app.conf.update(
    task_default_queue="default",
    task_routes={"app.tasks.*": {"queue": "default"}},
)
