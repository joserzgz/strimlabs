from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc

from db.base import async_session
from db.models import User, Channel, ModActionLog
from routers.auth import get_current_user

router = APIRouter()


@router.get("")
async def get_stats(
    channel_id: int = Query(None),
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        base = select(ModActionLog).join(Channel).where(Channel.user_id == user.id)
        if channel_id:
            base = base.where(ModActionLog.channel_id == channel_id)

        # Total actions
        total = await session.scalar(
            select(func.count()).select_from(ModActionLog).join(Channel).where(
                Channel.user_id == user.id,
                *([ModActionLog.channel_id == channel_id] if channel_id else []),
            )
        )

        # Breakdown by action type
        breakdown_q = (
            select(ModActionLog.action, func.count().label("count"))
            .join(Channel)
            .where(
                Channel.user_id == user.id,
                *([ModActionLog.channel_id == channel_id] if channel_id else []),
            )
            .group_by(ModActionLog.action)
        )
        breakdown_result = await session.execute(breakdown_q)
        breakdown = {row.action: row.count for row in breakdown_result}

        # Top offenders
        top_q = (
            select(ModActionLog.username, func.count().label("count"))
            .join(Channel)
            .where(
                Channel.user_id == user.id,
                *([ModActionLog.channel_id == channel_id] if channel_id else []),
            )
            .group_by(ModActionLog.username)
            .order_by(desc("count"))
            .limit(10)
        )
        top_result = await session.execute(top_q)
        top_offenders = [{"username": r.username, "count": r.count} for r in top_result]

    return {
        "total_actions": total or 0,
        "breakdown": breakdown,
        "top_offenders": top_offenders,
        "messages_this_month": user.messages_this_month,
    }
