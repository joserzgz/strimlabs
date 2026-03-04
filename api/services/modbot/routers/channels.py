import os
from datetime import datetime, timezone
from urllib.parse import urlencode

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func

from core.db import async_session, User, Platform
from core.auth.deps import get_current_user
from core.plan_limits import get_limits
from services.modbot.models import Channel

router = APIRouter()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5174")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_BOT_REDIRECT_URI = os.getenv("DISCORD_BOT_REDIRECT_URI", "")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_API = "https://discord.com/api/v10"


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
    ai_enabled: bool | None = None
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
        reset_at = user.messages_reset_at
        if reset_at and reset_at.tzinfo is None:
            reset_at = reset_at.replace(tzinfo=timezone.utc)
        if reset_at and (now - reset_at).days >= 30:
            user.messages_this_month = 0
            user.messages_reset_at = now

        if user.messages_this_month >= limits["messages_per_month"]:
            return {"allowed": False, "reason": "Monthly message limit reached"}

        user.messages_this_month += 1
        await session.commit()
    return {"allowed": True, "plan": user.plan}


# ── Discord Bot invite (requires JWT) ───────────────────────

@router.get("/discord-bot")
async def discord_bot_redirect(user: User = Depends(get_current_user)):
    permissions = 1 << 1 | 1 << 2 | 1 << 13 | 1 << 40  # BAN, KICK, MANAGE_MESSAGES, MODERATE_MEMBERS
    params = urlencode({
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_BOT_REDIRECT_URI,
        "response_type": "code",
        "scope": "bot identify",
        "permissions": str(permissions),
    })
    return {"url": f"https://discord.com/oauth2/authorize?{params}"}


@router.get("/discord-bot/callback")
async def discord_bot_callback(
    code: str = Query(None),
    guild_id: str = Query(None),
    user: User = Depends(get_current_user),
):
    if not guild_id:
        raise HTTPException(400, "No guild_id returned from Discord")

    # Fetch guild info via bot token
    guild_name = f"guild-{guild_id}"
    if DISCORD_BOT_TOKEN:
        try:
            async with aiohttp.ClientSession() as http:
                resp = await http.get(
                    f"{DISCORD_API}/guilds/{guild_id}",
                    headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
                )
                if resp.status == 200:
                    data = await resp.json()
                    guild_name = data.get("name", guild_name)
        except Exception:
            pass

    async with async_session() as session:
        channel = Channel(
            user_id=user.id,
            platform=Platform.discord,
            channel_name=guild_name,
            discord_guild_id=guild_id,
            is_active=True,
        )
        session.add(channel)
        await session.commit()

    return {"redirect": f"{FRONTEND_URL}/channels"}


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
        "ai_enabled": c.ai_enabled,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
