"""FastAPI application factory for Message Broker Service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import init_broker, router, shutdown_broker
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started_at = monotonic()
    await init_broker()
    yield
    await shutdown_broker()


def create_app() -> FastAPI:
    app = FastAPI(
        title="ASLP Message Broker Service",
        description="Asynchronous message distribution between ASLP services "
                    "backed by Apache Kafka. Publishes and consumes standard "
                    "StreamMessage payloads.",
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
    return app


app = create_app()
