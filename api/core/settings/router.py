from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.db import async_session, User
from core.auth.deps import get_current_user

router = APIRouter()


class SettingsUpdate(BaseModel):
    email: str | None = None


@router.get("")
async def get_settings(user: User = Depends(get_current_user)):
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
        "plan": user.plan,
        "subscription_status": user.subscription_status,
        "linked_accounts": accounts,
    }


@router.patch("")
async def update_settings(
    body: SettingsUpdate,
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        db_user = await session.get(User, user.id)
        if body.email is not None:
            db_user.email = body.email
        await session.commit()
    return {"ok": True}
