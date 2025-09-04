# app/models/message_schema.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, HttpUrl, field_validator
import xml.etree.ElementTree as ET


class MessageCreate(BaseModel):
    """Incoming message payload (XML as string)."""
    device_id: int = Field(gt=0)
    client_id: int = Field(gt=0)
    timestamp: Optional[datetime] = None   # leave None to let DB set default NOW()
    payload: str                            # raw XML

    model_config = ConfigDict(extra="forbid")

    @field_validator("timestamp")
    @classmethod
    def ensure_tz_awareness(cls, v: datetime | None) -> datetime | None:
        if v and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @field_validator("payload")
    @classmethod
    def must_be_well_formed_xml(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("payload must be a non-empty XML string")
        try:
            ET.fromstring(v)
        except ET.ParseError as e:
            raise ValueError(f"payload is not well-formed XML: {e}") from e
        return v

