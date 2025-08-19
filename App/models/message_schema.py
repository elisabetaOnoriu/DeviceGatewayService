from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class MessageCreate(BaseModel):
    device_id: int = Field(gt=0)
    client_id: int = Field(gt=0)
    timestamp: Optional[datetime] = None
    payload: Dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class SendResult(BaseModel):
    queue_url: str
    provider_message_id: str
    md5_of_body: Optional[str] = None
