import os
from urllib.parse import urlencode

import aiohttp
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select

from core.db import async_session, User, LinkedAccount, Platform
from core.auth.deps import create_jwt, get_current_user

router = APIRouter()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5174")

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")
TWITCH_REDIRECT_URI = os.getenv("TWITCH_REDIRECT_URI", "")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "")


# ── Twitch OAuth ─────────────────────────────────────────────

@router.get("/twitch")
async def twitch_redirect():
    params = urlencode({
        "client_id": TWITCH_CLIENT_ID,
        "redirect_uri": TWITCH_REDIRECT_URI,
        "response_type": "code",
        "scope": "user:read:email channel:moderate",
    })
    return RedirectResponse(f"https://id.twitch.tv/oauth2/authorize?{params}")


@router.get("/twitch/callback")
async def twitch_callback(code: str = Query(...)):
    async with aiohttp.ClientSession() as http:
        # Exchange code for token
        token_resp = await http.post(
            "https://id.twitch.tv/oauth2/token",
            data={
                "client_id": TWITCH_CLIENT_ID,
                "client_secret": TWITCH_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": TWITCH_REDIRECT_URI,
            },
        )
        if token_resp.status != 200:
            raise HTTPException(400, "Twitch token exchange failed")
        tokens = await token_resp.json()

        # Get user info
        user_resp = await http.get(
            "https://api.twitch.tv/helix/users",
            headers={
                "Authorization": f"Bearer {tokens['access_token']}",
                "Client-Id": TWITCH_CLIENT_ID,
            },
        )
        tw_data = (await user_resp.json())["data"][0]

    twitch_id = tw_data["id"]
    login = tw_data["login"]
    display = tw_data["display_name"]
    email = tw_data.get("email")
    avatar = tw_data.get("profile_image_url")

    async with async_session() as session:
        # Find existing linked account
        result = await session.execute(
            select(LinkedAccount).where(
                LinkedAccount.platform == Platform.twitch,
                LinkedAccount.platform_user_id == twitch_id,
            )
        )
        linked = result.scalar_one_or_none()

        if linked:
            user = await session.get(User, linked.user_id)
            linked.access_token = tokens["access_token"]
            linked.refresh_token = tokens.get("refresh_token")
            linked.platform_username = login
            linked.platform_display_name = display
            linked.platform_avatar_url = avatar
        else:
            user = User(email=email, avatar_url=avatar)
            session.add(user)
            await session.flush()
            linked = LinkedAccount(
                user_id=user.id,
                platform=Platform.twitch,
                platform_user_id=twitch_id,
                platform_username=login,
                platform_display_name=display,
                platform_avatar_url=avatar,
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token"),
            )
            session.add(linked)

        if email and not user.email:
            user.email = email
        if avatar:
            user.avatar_url = avatar
        await session.commit()

        jwt_token = create_jwt(user.id)
    return RedirectResponse(f"{FRONTEND_URL}/dashboard?token={jwt_token}")


# ── Discord OAuth ────────────────────────────────────────────

DISCORD_API = "https://discord.com/api/v10"


@router.get("/discord/bot")
async def discord_bot_invite():
    params = urlencode({
        "client_id": DISCORD_CLIENT_ID,
        "permissions": "1099511635974",
        "scope": "bot",
    })
    return {"url": f"https://discord.com/oauth2/authorize?{params}"}


@router.get("/discord")
async def discord_redirect():
    params = urlencode({
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify email",
    })
    return RedirectResponse(f"https://discord.com/oauth2/authorize?{params}")


@router.get("/discord/callback")
async def discord_callback(code: str = Query(...)):
    async with aiohttp.ClientSession() as http:
        token_resp = await http.post(
            f"{DISCORD_API}/oauth2/token",
            data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": DISCORD_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_resp.status != 200:
            raise HTTPException(400, "Discord token exchange failed")
        tokens = await token_resp.json()

        user_resp = await http.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        dc_data = await user_resp.json()

    discord_id = dc_data["id"]
    username = dc_data["username"]
    display = dc_data.get("global_name", username)
    email = dc_data.get("email")
    avatar_hash = dc_data.get("avatar")
    avatar_url = (
        f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png"
        if avatar_hash else None
    )

    async with async_session() as session:
        result = await session.execute(
            select(LinkedAccount).where(
                LinkedAccount.platform == Platform.discord,
                LinkedAccount.platform_user_id == discord_id,
            )
        )
        linked = result.scalar_one_or_none()

        if linked:
            user = await session.get(User, linked.user_id)
            linked.access_token = tokens["access_token"]
            linked.refresh_token = tokens.get("refresh_token")
            linked.platform_username = username
            linked.platform_display_name = display
            linked.platform_avatar_url = avatar_url
        else:
            user = User(email=email, avatar_url=avatar_url)
            session.add(user)
            await session.flush()
            linked = LinkedAccount(
                user_id=user.id,
                platform=Platform.discord,
                platform_user_id=discord_id,
                platform_username=username,
                platform_display_name=display,
                platform_avatar_url=avatar_url,
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token"),
            )
            session.add(linked)

        if email and not user.email:
            user.email = email
        if avatar_url:
            user.avatar_url = avatar_url
        await session.commit()

        jwt_token = create_jwt(user.id)
    return RedirectResponse(f"{FRONTEND_URL}/dashboard?token={jwt_token}")


# ── Me & Admin ───────────────────────────────────────────────

@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    accounts = []
    for la in user.linked_accounts:
        accounts.append({
            "platform": la.platform.value,
            "username": la.platform_username,
            "display_name": la.platform_display_name,
            "avatar_url": la.platform_avatar_url,
        })
    return {
        "id": user.id,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "plan": user.plan,
        "subscription_status": user.subscription_status,
        "is_admin": user.is_admin,
        "linked_accounts": accounts,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


class AdminLogin(BaseModel):
    password: str


@router.post("/admin/login")
async def admin_login(body: AdminLogin):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.is_admin == True))
        admin = result.scalar_one_or_none()
        if not admin or not admin.hashed_password:
            raise HTTPException(401, "Invalid credentials")
        if not bcrypt.checkpw(body.password.encode(), admin.hashed_password.encode()):
            raise HTTPException(401, "Invalid credentials")
        return {"token": create_jwt(admin.id)}
