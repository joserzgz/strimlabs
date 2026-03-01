from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from db.base import async_session
from db.models import User, Channel, BlacklistEntry
from routers.auth import get_current_user

router = APIRouter()


class BlacklistCreate(BaseModel):
    channel_id: int
    pattern: str


@router.get("")
async def get_blacklist(
    channel_id: int = Query(...),
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        channel = await session.get(Channel, channel_id)
        if not channel or channel.user_id != user.id:
            raise HTTPException(404, "Channel not found")
        result = await session.execute(
            select(BlacklistEntry).where(BlacklistEntry.channel_id == channel_id)
        )
        entries = result.scalars().all()
    return [
        {
            "id": e.id,
            "pattern": e.pattern,
            "added_by": e.added_by,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]


@router.post("")
async def add_blacklist(
    body: BlacklistCreate,
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        channel = await session.get(Channel, body.channel_id)
        if not channel or channel.user_id != user.id:
            raise HTTPException(404, "Channel not found")
        entry = BlacklistEntry(
            channel_id=body.channel_id,
            pattern=body.pattern,
            added_by=user.email or "user",
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
    return {"id": entry.id, "pattern": entry.pattern}


@router.delete("/{entry_id}")
async def delete_blacklist(
    entry_id: int,
    user: User = Depends(get_current_user),
):
    async with async_session() as session:
        entry = await session.get(BlacklistEntry, entry_id)
        if not entry:
            raise HTTPException(404, "Entry not found")
        channel = await session.get(Channel, entry.channel_id)
        if not channel or channel.user_id != user.id:
            raise HTTPException(403, "Not your channel")
        await session.delete(entry)
        await session.commit()
    return {"ok": True}
