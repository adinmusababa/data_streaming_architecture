"""Pydantic schemas for the Configuration Service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ConfigItem(BaseModel):
    """A single service configuration item."""

    service_name: str = Field(..., min_length=1)
    config_data: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ConfigUpsertRequest(BaseModel):
    """Request body for creating or updating configuration."""

    service_name: str = Field(..., min_length=1)
    config_data: dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class ConfigListResponse(BaseModel):
    """Response containing a list of configuration items."""

    items: list[ConfigItem] = Field(default_factory=list)
    total: int = 0


class ConfigReloadRequest(BaseModel):
    """Request body for configuration reload."""

    service_name: Optional[str] = None
    force: bool = False


class ConfigReloadResponse(BaseModel):
    """Response returned after a reload operation."""

    reloaded: bool
    service_name: Optional[str] = None
    total_loaded: int = 0
    message: str = "Configuration reloaded successfully."


class HealthResponse(BaseModel):
    """Health-check response."""

    service: str = "configuration-service"
    status: str = "running"
    version: str
    database: str = "connected"
    uptime_seconds: float = 0.0


class StatusResponse(BaseModel):
    """Operational status response."""

    service: str = "configuration-service"
    status: str = "running"
    version: str
    uptime_seconds: float = 0.0
    total_configs: int = 0
    cached_configs: int = 0
    database_status: str = "connected"
    last_reload_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    """Simple success or error message response."""

    success: bool = True
    message: str