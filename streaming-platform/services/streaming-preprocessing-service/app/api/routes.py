"""Minimal API routes for Streaming Preprocessing Service."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas import BootstrapResponse, ConfigReloadResponse, HealthResponse, ServiceStatus
from app.services.config_service import StreamingConfigService

router = APIRouter()

_config_service = StreamingConfigService()


async def get_config_service() -> StreamingConfigService:
    return _config_service


@router.get("/health", response_model=HealthResponse)
async def health(config_service: StreamingConfigService = Depends(get_config_service)):
    status = config_service.status()
    return HealthResponse(config_loaded=status["config_loaded"])


@router.get("/status", response_model=ServiceStatus)
async def status(config_service: StreamingConfigService = Depends(get_config_service)):
    return ServiceStatus(**config_service.status())


@router.post("/config/reload", response_model=ConfigReloadResponse)
async def reload_config(config_service: StreamingConfigService = Depends(get_config_service)):
    config = await config_service.reload()
    return ConfigReloadResponse(
        reloaded=True,
        message="Configuration reloaded successfully.",
        source_type=str(config.get("source_type", "csv")),
        batch_size=int(config.get("batch_size", 100)),
        polling_interval=float(config.get("polling_interval", 1.0)),
        publish_topic=str(config.get("publish_topic", "stream_data")),
    )


@router.get("/bootstrap", response_model=BootstrapResponse)
async def bootstrap(config_service: StreamingConfigService = Depends(get_config_service)):
    config = await config_service.load()
    return BootstrapResponse(success=True, message="Config loaded", config=config)
