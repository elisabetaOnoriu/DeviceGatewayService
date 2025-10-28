from __future__ import annotations
import time
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class DeviceData(BaseModel):
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Humidity in percent")
    status: Optional[str] = Field(default="online", description="Status device")


class DeviceMessage(BaseModel):
    """Model for device generated messages"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    device_id: int
    timestamp: float = Field(default_factory=time.time)
    data: Optional[DeviceData] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.data is None:
            t = 20.0 + (self.device_id % 10)
            h = 50.0 + (self.device_id % 20)
            self.data = DeviceData(temperature=round(t, 2), humidity=round(h, 2))

    def to_dict(self) -> dict:
        return self.model_dump()
