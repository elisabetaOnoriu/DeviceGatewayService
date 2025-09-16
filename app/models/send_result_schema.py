from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator
import re


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
