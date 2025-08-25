from __future__ import annotations
from sqlalchemy import String, ForeignKey, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from .status import Status


class Device(Base):
    __tablename__ = "devices"

    device_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.client_id"), nullable=False)
    status: Mapped[Status] = mapped_column(Enum(Status), nullable=False, default=Status.DISCONNECTED)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    payload: Mapped[str | None] = mapped_column(String, nullable=True)
