from __future__ import annotations
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from .base import Base

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.client_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")  # timestamptz in Postgres
    )
    payload = Column(JSONB, nullable=False)

    # (optional) relationships, only if you have the mapped classes
    # device = relationship("Device", backref="messages")
    # client = relationship("Client", backref="messages")

# useful indexes
Index("ix_messages_device_ts", Message.device_id, Message.timestamp.desc())
# fast searches in JSONB (optional)
Index("ix_messages_payload_gin", Message.payload, postgresql_using="gin")
