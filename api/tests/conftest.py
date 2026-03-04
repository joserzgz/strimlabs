import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Set env vars before importing app modules
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_EXPIRE_HOURS", "1")
os.environ.setdefault("ADMIN_PASSWORD", "testpass")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_fake")
os.environ.setdefault("STRIPE_PRICE_ID", "price_fake")
os.environ.setdefault("MP_ACCESS_TOKEN", "TEST-fake")

from httpx import AsyncClient, ASGITransport
from core.db.base import Base
from core.db import models as _models  # noqa: ensure models registered
import services.modbot.models as _mb_models  # noqa
from core.auth.deps import create_jwt

# ── Test DB engine (SQLite async in-memory) ──────────────────
test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db(monkeypatch):
    """Create tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Patch async_session everywhere it's imported
    monkeypatch.setattr("core.db.base.async_session", TestSession)
    monkeypatch.setattr("core.db.async_session", TestSession)
    monkeypatch.setattr("core.auth.deps.async_session", TestSession)
    monkeypatch.setattr("core.settings.router.async_session", TestSession)
    monkeypatch.setattr("core.billing.router.async_session", TestSession)
    monkeypatch.setattr("services.modbot.routers.channels.async_session", TestSession)
    monkeypatch.setattr("services.modbot.routers.blacklist.async_session", TestSession)
    monkeypatch.setattr("services.modbot.routers.history.async_session", TestSession)
    monkeypatch.setattr("services.modbot.routers.stats.async_session", TestSession)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    """Provide a test DB session."""
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db):
    """Create a free-plan test user."""
    from core.db.models import User
    user = User(email="test@example.com", plan="free")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def pro_user(db):
    """Create a pro-plan test user."""
    from core.db.models import User
    user = User(email="pro@example.com", plan="pro")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db):
    """Create an admin user with hashed password."""
    import bcrypt
    from core.db.models import User
    hashed = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode()
    user = User(
        email="admin@strimlabs.com",
        is_admin=True,
        hashed_password=hashed,
        plan="pro",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def make_token(user_id: int) -> str:
    return create_jwt(user_id)


def auth_headers(user_id: int) -> dict:
    return {"Authorization": f"Bearer {make_token(user_id)}"}


@pytest_asyncio.fixture
async def test_channel(db, test_user):
    """Create a Twitch channel for test_user."""
    from services.modbot.models import Channel
    from core.db.models import Platform
    ch = Channel(
        user_id=test_user.id,
        platform=Platform.twitch,
        channel_name="test_channel",
        is_active=True,
    )
    db.add(ch)
    await db.commit()
    await db.refresh(ch)
    return ch


@pytest_asyncio.fixture
async def client():
    """Async HTTP test client for the FastAPI app."""
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
