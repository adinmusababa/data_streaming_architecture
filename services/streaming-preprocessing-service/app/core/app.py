"""FastAPI application factory for Streaming Preprocessing Service with preprocessing pipeline."""

from __future__ import annotations

from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started_at = monotonic()

    # Bootstrap configuration and create the shared orchestrator so the
    # config loaded here is the same one used by /stream/start.
    try:
        from app.api.routes import get_orchestrator, get_config_service
        config_service = await get_config_service()
        await config_service.load()
        await get_orchestrator()
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Could not bootstrap orchestrator on startup: %s", exc)

    yield

    # Cleanup: stop any running stream
    try:
        from app.api.routes import get_orchestrator
        orch = await get_orchestrator()
        if orch.is_running:
            await orch.stop()
    except Exception:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="ASLP Streaming Preprocessing Service",
        description="Reads preprocessing configuration from the Configuration Service "
                    "and streams data from CSV sources to the Message Broker.",
        version=settings.SERVICE_VERSION,
        lifespan=lifespan,
    )

    from app.api.routes import router
    app.include_router(router)
    return app


app = create_app()
