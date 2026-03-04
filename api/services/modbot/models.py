from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, Float, Text, DateTime,
    ForeignKey, Enum, JSON,
)
from sqlalchemy.orm import relationship
from core.db.base import Base
from core.db.models import Platform


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    channel_name = Column(String(255), nullable=True)
    discord_guild_id = Column(String(255), nullable=True)
    discord_channel_ids = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    mod_action = Column(String(20), default="timeout")
    timeout_seconds = Column(Integer, default=600)
    toxicity_threshold = Column(Float, default=0.8)
    ai_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="channels")
    blacklist_entries = relationship("BlacklistEntry", back_populates="channel", cascade="all, delete-orphan")
    mod_action_logs = relationship("ModActionLog", back_populates="channel", cascade="all, delete-orphan")


class BlacklistEntry(Base):
    __tablename__ = "blacklist_entries"

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    pattern = Column(Text, nullable=False)
    added_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    channel = relationship("Channel", back_populates="blacklist_entries")


class ModActionLog(Base):
    __tablename__ = "mod_action_logs"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    action = Column(String(20), nullable=False)
    reason = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    channel = relationship("Channel", back_populates="mod_action_logs")
