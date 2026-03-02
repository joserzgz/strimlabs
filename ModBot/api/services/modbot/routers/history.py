from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc

from core.db import async_session, User
from core.auth.deps import get_current_user
from core.plan_limits import get_limits
from services.modbot.models import Channel, ModActionLog

router = APIRouter()


@router.get("")
async def get_history(
    channel_id: int = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    limits = get_limits(user.plan)
    if not limits["has_history"]:
        raise HTTPException(403, "History requires Pro plan")

    async with async_session() as session:
        q = select(ModActionLog).join(Channel).where(Channel.user_id == user.id)
        if channel_id:
            q = q.where(ModActionLog.channel_id == channel_id)
        q = q.order_by(desc(ModActionLog.created_at))
        q = q.offset((page - 1) * limit).limit(limit)
        result = await session.execute(q)
        logs = result.scalars().all()

    out = []
    for log in logs:
        out.append({
            "id": log.id,
            "channel_id": log.channel_id,
            "username": log.username,
            "message": log.message,
            "action": log.action,
            "reason": log.reason,
            "score": log.score,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })
    return out


class InternalLog(BaseModel):
    channel_id: int
    username: str
    message: str
    action: str
    reason: str | None = None
    score: float | None = None


@router.post("/internal")
async def log_action(body: InternalLog):
    async with async_session() as session:
        log = ModActionLog(
            channel_id=body.channel_id,
            username=body.username,
            message=body.message,
            action=body.action,
            reason=body.reason,
            score=body.score,
        )
        session.add(log)
        await session.commit()
    return {"ok": True}
