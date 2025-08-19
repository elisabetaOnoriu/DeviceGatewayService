# app/models/message_schema.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, HttpUrl, field_validator
import xml.etree.ElementTree as ET
import re


class MessageCreate(BaseModel):
    """Incoming message payload (XML as string)."""
    device_id: int = Field(gt=0)
    client_id: int = Field(gt=0)
    timestamp: Optional[datetime] = None   # leave None to let DB set default NOW()
    payload: str                            # raw XML

    model_config = ConfigDict(extra="forbid")

    @field_validator("timestamp")
    @classmethod
    def ensure_tz_awareness(cls, v: Optional[datetime]) -> Optional[datetime]:
        # Accept naive datetimes but normalize to UTC to avoid surprises.
        if v and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @field_validator("payload")
    @classmethod
    def must_be_well_formed_xml(cls, v: str) -> str:
        # Minimal check: non-empty and parsable as XML
        if not isinstance(v, str) or not v.strip():
            raise ValueError("payload must be a non-empty XML string")
        try:
            root = ET.fromstring(v.encode("utf-8"))
        except Exception as e:
            raise ValueError(f"payload is not well-formed XML: {e}") from e
        # Optional: require specific root name
        # if root.tag.split('}')[-1] != "Message":
        #     raise ValueError("payload root element must be <Message>")
        return v


class SendResult(BaseModel):
    """Result after sending the message to a queue."""
    queue_url: HttpUrl
    provider_message_id: str
    md5_of_body: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("md5_of_body")
    @classmethod
    def validate_md5(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.fullmatch(r"[a-fA-F0-9]{32}", v):
            raise ValueError("md5_of_body must be a 32-hex-digit MD5 string")
        return v
