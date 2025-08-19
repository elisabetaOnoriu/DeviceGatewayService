import boto3
from app.utils.env_loader import get_env

def get_sqs_client():
    return boto3.client(
        "sqs",
        aws_access_key_id=get_env("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=get_env("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=get_env("AWS_REGION", "us-east-1"),
        endpoint_url=get_env("SQS_ENDPOINT_URL", "http://localhost:4566"),
    )

def send_message(queue_url: str, body: str, attributes: dict | None = None):
    sqs = get_sqs_client()
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=body,
        MessageAttributes=attributes or {}
    )
    return response
