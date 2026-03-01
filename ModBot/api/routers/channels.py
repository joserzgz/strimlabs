import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func

from db.base import async_session
from db.models import User, Channel, Platform
from plan_limits import get_limits
from routers.auth import get_current_user

router = APIRouter()


class ChannelCreate(BaseModel):
    platform: str
    channel_name: str | None = None
    discord_guild_id: str | None = None
    discord_channel_ids: list[str] | None = None


class ChannelUpdate(BaseModel):
    is_active: bool | None = None
    mod_action: str | None = None
    timeout_seconds: int | None = None
    toxicity_threshold: float | None = None
    discord_channel_ids: list[str] | None = None


@router.get("/me")
async def get_my_channels(
    platform: str | None = None,
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        q = select(Channel).where(Channel.user_id == user.id)
        if platform:
            q = q.where(Channel.platform == Platform(platform))
        result = await session.execute(q)
        channels = result.scalars().all()
    return [_channel_dict(c) for c in channels]


@router.post("/me")
async def create_channel(
    body: ChannelCreate,
    user: User = Depends(get_current_user),
):
    limits = get_limits(user.plan)
    async with async_session() as session:
        count = await session.scalar(
            select(func.count()).select_from(Channel).where(Channel.user_id == user.id)
        )
        if count >= limits["max_channels"]:
            raise HTTPException(403, f"Plan {user.plan} allows max {limits['max_channels']} channel(s)")

        plat = Platform(body.platform)
        if plat == Platform.twitch and not body.channel_name:
            raise HTTPException(400, "channel_name required for Twitch")
        if plat == Platform.discord and not body.discord_guild_id:
            raise HTTPException(400, "discord_guild_id required for Discord")

        channel = Channel(
            user_id=user.id,
            platform=plat,
            channel_name=body.channel_name,
            discord_guild_id=body.discord_guild_id,
            discord_channel_ids=body.discord_channel_ids,
        )
        session.add(channel)
        await session.commit()
        await session.refresh(channel)
    return _channel_dict(channel)


@router.patch("/me/{channel_id}")
async def update_channel(
    channel_id: int,
    body: ChannelUpdate,
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        channel = await session.get(Channel, channel_id)
        if not channel or channel.user_id != user.id:
            raise HTTPException(404, "Channel not found")
        for field, val in body.model_dump(exclude_none=True).items():
            setattr(channel, field, val)
        await session.commit()
        await session.refresh(channel)
    return _channel_dict(channel)


@router.delete("/me/{channel_id}")
async def delete_channel(
    channel_id: int,
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        channel = await session.get(Channel, channel_id)
        if not channel or channel.user_id != user.id:
            raise HTTPException(404, "Channel not found")
        await session.delete(channel)
        await session.commit()
    return {"ok": True}


# ── Internal endpoints (for bots) ───────────────────────────

@router.get("/active")
async def get_active_channels(platform: str = Query(...)):
    async with async_session() as session:
        result = await session.execute(
            select(Channel).where(
                Channel.is_active == True,
                Channel.platform == Platform(platform),
            )
        )
        channels = result.scalars().all()
    out = []
    for c in channels:
        user = None
        async with async_session() as session:
            user = await session.get(User, c.user_id)
        out.append({
            **_channel_dict(c),
            "plan": user.plan if user else "free",
        })
    return out


@router.get("/{channel_id}/quota")
async def check_quota(channel_id: int):
    async with async_session() as session:
        channel = await session.get(Channel, channel_id)
        if not channel:
            raise HTTPException(404, "Channel not found")
        user = await session.get(User, channel.user_id)
        if not user:
            raise HTTPException(404, "User not found")

        limits = get_limits(user.plan)
        now = datetime.now(timezone.utc)

        # Reset monthly counter if needed
        if user.messages_reset_at and (now - user.messages_reset_at).days >= 30:
            user.messages_this_month = 0
            user.messages_reset_at = now

        if user.messages_this_month >= limits["messages_per_month"]:
            return {"allowed": False, "reason": "Monthly message limit reached"}

        user.messages_this_month += 1
        await session.commit()
    return {"allowed": True, "plan": user.plan}


def _channel_dict(c: Channel) -> dict:
    return {
        "id": c.id,
        "platform": c.platform.value,
        "channel_name": c.channel_name,
        "discord_guild_id": c.discord_guild_id,
        "discord_channel_ids": c.discord_channel_ids,
        "is_active": c.is_active,
        "mod_action": c.mod_action,
        "timeout_seconds": c.timeout_seconds,
        "toxicity_threshold": c.toxicity_threshold,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
