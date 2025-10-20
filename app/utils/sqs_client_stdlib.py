import os
import boto3

def get_sqs():
    kwargs = {"region_name": os.getenv("AWS_REGION", "us-east-1")}
    endpoint = os.getenv("SQS_ENDPOINT_URL")

    if endpoint:
        kwargs.update({
            "endpoint_url": endpoint,
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", "test"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        })

    return boto3.client("sqs", **kwargs)

def send_message(queue_url: str, body: str, attributes: dict | None = None):
    return get_sqs().send_message(
        QueueUrl=queue_url,
        MessageBody=body,
        MessageAttributes=attributes or {},
    )
