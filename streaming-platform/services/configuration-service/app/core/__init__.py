"""FastAPI application factory for the Configuration Service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.database import close_db, init_db, async_session_maker
from app.services import ConfigurationService
from app.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    app.state.started_at = monotonic()
    await init_db()
    async with async_session_maker() as session:
        service = ConfigurationService(session)
        await service.seed_defaults()
    yield
    await close_db()


app = FastAPI(
    title="ASLP Configuration Service",
    description="Centralized configuration storage for the ASLP platform",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
