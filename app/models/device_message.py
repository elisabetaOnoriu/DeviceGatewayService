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
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique Message ID")
    device_id: int = Field(..., description="ID device")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp")
    data: DeviceData = Field(..., description="Date senzori")
    
    def to_json(self) -> str:
        return self.model_dump_json()
    
    def to_dict(self) -> dict:
        return self.model_dump()
    
    @classmethod
    def create_for_device(cls, device_id: int) -> DeviceMessage:
        data = DeviceData(
            temperature=20 + (device_id % 10),
            humidity=50 + (device_id % 20),
            status="online",
        )
        
        return cls(device_id=device_id, data=data)