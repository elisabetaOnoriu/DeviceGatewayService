from __future__ import annotations
from typing import Protocol

class SQSProtocol(Protocol):
    def send_message(self, *, QueueUrl: str, MessageBody: str) -> dict: ...

def send_xml(sqs: SQSProtocol, queue_url: str, xml_str: str) -> str:
    """
    Sends an XML message to the SQS queue and returns the MessageId (if available).
    """
    resp = sqs.send_message(QueueUrl=queue_url, MessageBody=xml_str)
    return resp.get("MessageId", "")
