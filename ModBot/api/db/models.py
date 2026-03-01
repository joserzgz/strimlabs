import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, Float, Text, DateTime,
    ForeignKey, Enum, JSON, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .base import Base


class Platform(str, enum.Enum):
    twitch = "twitch"
    discord = "discord"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    plan = Column(String(20), default="free")
    subscription_status = Column(String(20), default="active")
    subscription_id = Column(String(255), nullable=True)
    payment_provider = Column(String(20), nullable=True)
    plan_start = Column(DateTime(timezone=True), nullable=True)
    plan_end = Column(DateTime(timezone=True), nullable=True)
    is_admin = Column(Boolean, default=False)
    hashed_password = Column(String(255), nullable=True)
    messages_this_month = Column(Integer, default=0)
    messages_reset_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    linked_accounts = relationship("LinkedAccount", back_populates="user", lazy="selectin")
    channels = relationship("Channel", back_populates="user", lazy="selectin")


class LinkedAccount(Base):
    __tablename__ = "linked_accounts"
    __table_args__ = (
        UniqueConstraint("platform", "platform_user_id", name="uq_platform_user"),
        UniqueConstraint("user_id", "platform", name="uq_user_platform"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    platform_user_id = Column(String(255), nullable=False)
    platform_username = Column(String(255), nullable=False)
    platform_display_name = Column(String(255), nullable=True)
    platform_avatar_url = Column(Text, nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="linked_accounts")


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
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="channels")
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

    id = Column(BigInteger, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    action = Column(String(20), nullable=False)
    reason = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    channel = relationship("Channel", back_populates="mod_action_logs")
