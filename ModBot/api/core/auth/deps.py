import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request

from core.db import async_session, User

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "8"))


def create_jwt(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


async def get_current_user(request: Request) -> User:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = auth_header[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")

    async with async_session() as session:
        user = await session.get(User, payload["sub"])
        if not user:
            raise HTTPException(401, "User not found")
        return user
