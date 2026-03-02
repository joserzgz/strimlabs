import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime,
    ForeignKey, Enum, UniqueConstraint,
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
