"""FastAPI application for Streaming Preprocessing Service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.services.config_service import StreamingConfigService

config_service = StreamingConfigService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started_at = monotonic()
    await config_service.load()
    yield


app = FastAPI(
    title="ASLP Streaming Preprocessing Service",
    description="Reads preprocessing configuration from the Configuration Service",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

app.include_router(router)
