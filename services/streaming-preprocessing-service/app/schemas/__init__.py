"""Schemas for Streaming Preprocessing Service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class StreamingConfig(BaseModel):
    """Runtime configuration for the preprocessing service."""

    source_type: str = "csv"
    batch_size: int = 100
    polling_interval: float = 1.0
    preprocessing_pipeline: list[str] = Field(default_factory=lambda: ["validation", "cleaning", "transformation"])
    publish_topic: str = "stream_data"
    retry_count: int = 3
    config_source: str = "configuration-service"
    updated_at: Optional[datetime] = None


class ServiceStatus(BaseModel):
    """Operational status for the service."""

    service: str = "streaming-preprocessing-service"
    status: str = "running"
    config_loaded: bool = False
    config_source: str = "configuration-service"
    last_reload_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    """Health response for the service."""

    service: str = "streaming-preprocessing-service"
    status: str = "running"
    config_loaded: bool = False


class ConfigReloadResponse(BaseModel):
    """Response for config reload."""

    reloaded: bool
    message: str
    source_type: str
    batch_size: int
    polling_interval: float
    publish_topic: str


class BootstrapResponse(BaseModel):
    """Bootstrap response returned on startup diagnostics."""

    success: bool
    message: str
    config: dict[str, Any]


# -- Milestone 3 streaming schemas --

from app.schemas.streaming import (
    StreamStartRequest,
    StreamStatusResponse,
    StreamStatisticsResponse,
    StreamStopResponse,
)

__all__ = [
    "StreamingConfig",
    "ServiceStatus",
    "HealthResponse",
    "ConfigReloadResponse",
    "BootstrapResponse",
    # Streaming
    "StreamStartRequest",
    "StreamStatusResponse",
    "StreamStatisticsResponse",
    "StreamStopResponse",
]
