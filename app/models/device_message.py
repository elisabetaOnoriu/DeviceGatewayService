from __future__ import annotations
import time
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class DeviceData(BaseModel):
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Humidity in percent")
    status: Optional[str] = Field(default="online", description="Status device")


class DeviceMessage(BaseModel):
    """Model for device generated messages"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique Message ID")
    device_id: int = Field(..., description="ID device")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp")
    data: Optional[DeviceData] = Field(default=None, description="Sensor data")

    @model_validator(mode="after")
    def _autofill(self) -> "DeviceMessage":
        if self.data is None:
            t = 20.0 + (self.device_id % 10)
            h = 50.0 + float(self.device_id % 20)
            self.data = DeviceData(temperature=round(t, 2), humidity=round(h, 2), status="online")
        return self
    
    def to_dict(self) -> dict:
        return self.model_dump()
