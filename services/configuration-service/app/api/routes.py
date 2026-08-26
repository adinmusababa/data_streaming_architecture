"""REST API routes for the Configuration Service."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.schemas import (
    ConfigItem,
    ConfigListResponse,
    ConfigReloadRequest,
    ConfigReloadResponse,
    ConfigUpsertRequest,
    HealthResponse,
    MessageResponse,
    StatusResponse,
)
from shared_sdk.responses import SuccessResponse
from app.services import ConfigurationService

router = APIRouter()


def _to_config_item(data: dict) -> ConfigItem:
    return ConfigItem(
        service_name=data["service_name"],
        config_data=data["config_data"],
        version=data["version"],
        description=data.get("description"),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


async def get_configuration_service(session: AsyncSession = Depends(get_session)) -> ConfigurationService:
    return ConfigurationService(session)


@router.get("/api/v1/config", response_model=ConfigListResponse)
@router.get("/config", response_model=ConfigListResponse, include_in_schema=False)
async def get_configs(
    service_name: str | None = Query(default=None),
    configuration_service: ConfigurationService = Depends(get_configuration_service),
):
    """Return all configs or a single service config if requested."""
    if service_name:
        item = await configuration_service.get_one(service_name)
        if item is None:
            raise HTTPException(status_code=404, detail=f"Configuration not found for '{service_name}'")
        return ConfigListResponse(items=[_to_config_item(item)], total=1)

    items = [_to_config_item(item) for item in await configuration_service.get_all()]
    return ConfigListResponse(items=items, total=len(items))


@router.get("/api/v1/config/{service_name}", response_model=SuccessResponse)
async def get_service_config(
    service_name: str,
    configuration_service: ConfigurationService = Depends(get_configuration_service),
):
    """Return one service config in the shared SDK response format.

    Consumed by shared_sdk ConfigLoader.refresh().
    """
    item = await configuration_service.get_one(service_name)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Configuration not found for '{service_name}'")
    return SuccessResponse(message=f"Configuration for '{service_name}'", data=item["config_data"])


@router.put("/api/v1/config", response_model=ConfigItem)
@router.put("/config", response_model=ConfigItem, include_in_schema=False)
async def put_config(
    payload: ConfigUpsertRequest,
    configuration_service: ConfigurationService = Depends(get_configuration_service),
):
    """Create or update a service configuration."""
    item = await configuration_service.upsert(
        service_name=payload.service_name,
        config_data=payload.config_data,
        description=payload.description,
    )
    return _to_config_item(item)


@router.post("/api/v1/config/reload", response_model=ConfigReloadResponse)
@router.post("/config/reload", response_model=ConfigReloadResponse, include_in_schema=False)
async def reload_config(
    payload: ConfigReloadRequest,
    configuration_service: ConfigurationService = Depends(get_configuration_service),
):
    """Reload configuration cache from storage."""
    result = await configuration_service.reload(service_name=payload.service_name, force=payload.force)
    return ConfigReloadResponse(**result)


@router.get("/api/v1/health", response_model=HealthResponse)
@router.get("/health", response_model=HealthResponse, include_in_schema=False)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        version=settings.SERVICE_VERSION,
        database="connected",
        uptime_seconds=0.0,
    )


@router.get("/api/v1/status", response_model=StatusResponse)
@router.get("/status", response_model=StatusResponse, include_in_schema=False)
async def status_endpoint(
    configuration_service: ConfigurationService = Depends(get_configuration_service),
):
    """Operational status endpoint."""
    stats = await configuration_service.stats()
    return StatusResponse(**stats)


@router.post("/api/v1/config/delete", response_model=MessageResponse)
@router.delete("/config", response_model=MessageResponse, include_in_schema=False)
async def delete_config(
    service_name: str = Query(...),
    configuration_service: ConfigurationService = Depends(get_configuration_service),
):
    """Delete a configuration entry."""
    deleted = await configuration_service.delete(service_name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Configuration not found for '{service_name}'")
    return MessageResponse(success=True, message=f"Configuration deleted for '{service_name}'")
