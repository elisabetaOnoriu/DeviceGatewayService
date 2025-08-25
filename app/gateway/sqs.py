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
    depending on the variables in settings
    """
    return boto3.client(
        "sqs",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        endpoint_url=settings.endpoint,  # pentru LocalStack / endpoint custom
    )


def resolve_queue_url(sqs: SQSProtocol) -> str:
    """
    Attempts to retrieve the QueueUrl via the SQS API.
    If it fails (e.g., in certain LocalStack setups),
    it falls back to the format: {endpoint}/{account_id}/{queue_name}.
    """
    try:
        return sqs.get_queue_url(QueueName=settings.QUEUE_NAME)["QueueUrl"]
    except (ClientError, BotoCoreError):
        fallback = f"{settings.endpoint.rstrip('/')}/{settings.ACCOUNT_ID}/{settings.QUEUE_NAME}"
        log.warning("Falling back to LocalStack-style queue URL: %s", fallback)
        return fallback
