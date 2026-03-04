import os
import bcrypt
from sqlalchemy import select, text
from .base import engine, async_session, Base
from .models import User


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Add columns that create_all won't add to existing tables
    async with engine.begin() as conn:
        try:
            await conn.execute(text(
                "ALTER TABLE channels ADD COLUMN IF NOT EXISTS ai_enabled BOOLEAN DEFAULT TRUE"
            ))
        except Exception:
            pass

    admin_pw = os.getenv("ADMIN_PASSWORD", "admin1234")
    hashed = bcrypt.hashpw(admin_pw.encode(), bcrypt.gensalt()).decode()

    async with async_session() as session:
        result = await session.execute(select(User).where(User.is_admin == True))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin@strimlabs.com",
                is_admin=True,
                hashed_password=hashed,
                plan="pro",
            )
            session.add(admin)
            await session.commit()
