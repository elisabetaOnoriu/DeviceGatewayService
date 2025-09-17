from __future__ import annotations
import logging
from typing import Protocol

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config.settings import settings

log = logging.getLogger(__name__)


class SQSProtocol(Protocol):
    def get_queue_url(self, *, QueueName: str) -> dict: ...
    def send_message(self, *, QueueUrl: str, MessageBody: str) -> dict: ...


def make_sqs_client() -> SQSProtocol:
    """
    Creates a boto3 SQS client configured for either real AWS or LocalStack,
    depending on values from settings.AWS (nested settings).
    """
    return boto3.client(
        "sqs",
        aws_access_key_id=settings.AWS.ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS.SECRET_ACCESS_KEY,
        region_name=settings.AWS.AWS_REGION,
        endpoint_url=settings.AWS.endpoint,
    )


def resolve_queue_url(sqs: SQSProtocol) -> str:
    """
    Tries to retrieve the QueueUrl via SQS API. On failure (e.g., LocalStack quirks),
    falls back to: {endpoint}/{account_id}/{queue_name}.
    """
    try:
        queue_url = sqs.get_queue_url(QueueName=settings.AWS.QUEUE_NAME)["QueueUrl"]
        return queue_url
    except (ClientError, BotoCoreError):
        fallback = f"{settings.AWS.endpoint.rstrip('/')}/{settings.AWS.ACCOUNT_ID}/{settings.AWS.QUEUE_NAME}"
        log.warning("Falling back to LocalStack-style queue URL: %s", fallback)
        return fallback
