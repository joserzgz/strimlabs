import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.init_db import init_db
from routers import auth, channels, blacklist, history, stats, settings, billing


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

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(blacklist.router, prefix="/api/blacklist", tags=["blacklist"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
