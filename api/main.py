import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.db.init_db import init_db

# Register service models with SQLAlchemy before creating tables
import services.modbot.models  # noqa

from core.auth.router import router as auth_router
from core.billing.router import router as billing_router
from core.settings.router import router as settings_router
from services.modbot.routers.channels import router as channels_router
from services.modbot.routers.blacklist import router as blacklist_router
from services.modbot.routers.history import router as history_router
from services.modbot.routers.stats import router as stats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Strimlabs ModBot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5174")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(billing_router, prefix="/api/billing", tags=["billing"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])

# ModBot
app.include_router(channels_router, prefix="/api/channels", tags=["modbot"])
app.include_router(blacklist_router, prefix="/api/blacklist", tags=["modbot"])
app.include_router(history_router, prefix="/api/history", tags=["modbot"])
app.include_router(stats_router, prefix="/api/stats", tags=["modbot"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
