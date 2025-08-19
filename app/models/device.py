from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from .base import Base
from .status import Status

class Device(Base):
    __tablename__ = "devices"

    device_id = Column(Integer, primary_key=True, index=True)
    client_id  = Column(Integer, ForeignKey("clients.client_id"), nullable=False)
    status     = Column(Enum(Status), nullable=False, default=Status.DISCONNECTED)
    location   = Column(String, nullable=True)
    payload    = Column(String, nullable=True)
