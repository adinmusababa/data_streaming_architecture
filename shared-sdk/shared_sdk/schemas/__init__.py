"""
Shared Pydantic schemas for ASLP services.
"""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseRequest(BaseModel):
    """Base request model with common configuration."""

    class Config:
        # Allow extra fields for flexibility
        extra = "allow"
        # Use enum values
        use_enum_values = True
        # Populate by name (alias support)
        populate_by_name = True


class BaseResponse(BaseModel):
    """Base response model - keeping for backward compatibility."""
    success: bool = True
    message: str = "Success"


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    sort: Optional[str] = Field(default=None, description="Sort field")
    order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")


class Metadata(BaseModel):
    """Standard metadata for resources."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1, ge=1)
    tags: Optional[dict[str, str]] = None


class HealthResponse(BaseModel):
    """Standard health check response."""
    service: str
    status: str = "running"
    version: str
    uptime: Optional[str] = None
    details: Optional[dict] = None


class StatusResponse(BaseModel):
    """Standard service status response."""
    service: str
    status: str
    started_at: datetime
    uptime_seconds: float
    active_connections: Optional[int] = None
    queue_size: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    details: Optional[dict] = None


class StatisticsResponse(BaseModel):
    """Standard statistics response."""
    service: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    last_request_at: Optional[datetime] = None
    custom_metrics: Optional[dict] = None


class ConfigurationResponse(BaseModel):
    """Configuration response model."""
    service: str
    config: dict
    last_updated: datetime


class ReloadConfigRequest(BaseModel):
    """Request to reload configuration."""
    force: bool = False