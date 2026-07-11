"""Database models for conversation memory."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, relationship

from jarvis.database import Base


class ChatSession(Base):
    """A conversation session containing multiple chat messages."""

    __tablename__ = "chat_sessions"

    id: Mapped[str] = Column(
        String(length=36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    messages: Mapped[list["ChatMessage"]]
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ChatMessage(Base):
    """A single message within a chat session."""

    __tablename__ = "chat_messages"

    id: Mapped[str] = Column(
        String(length=36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    session_id: Mapped[str] = Column(
        String(length=36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = Column(String(length=50), nullable=False)
    content: Mapped[str] = Column(Text, nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    session: Mapped[ChatSession] = relationship(
        "ChatSession",
        back_populates="messages",
        lazy="selectin",
    )
