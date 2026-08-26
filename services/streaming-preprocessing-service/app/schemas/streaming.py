"""Streaming-specific request/response schemas for the Preprocessing Service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class StreamStartRequest(BaseModel):
    """Request body to start a streaming session."""

    source_path: str = Field(
        default="sample_data/sample.csv",
        description="Path to the CSV data source",
    )
    source_type: str = Field(default="csv", description="Type of data source")
    batch_size: int = Field(default=10, ge=1, le=1000, description="Rows per batch")
    polling_interval: float = Field(
        default=1.0, ge=0.1, le=60.0, description="Seconds between batches"
    )
    publish_topic: str = Field(
        default="stream_data", description="Target broker queue/topic"
    )


class StreamStatusResponse(BaseModel):
    """Current streaming status."""

    is_running: bool = False
    source_path: Optional[str] = None
    source_type: Optional[str] = None
    total_rows_read: int = 0
    total_rows_estimated: int = 0
    total_published: int = 0
    total_failed: int = 0
    started_at: Optional[datetime] = None
    elapsed_seconds: float = 0.0


class StreamStatisticsResponse(BaseModel):
    """Detailed statistics for a completed or ongoing stream."""

    total_batches: int = 0
    total_rows: int = 0
    total_published: int = 0
    total_failed: int = 0
    success_rate: float = 1.0
    first_publish_at: Optional[datetime] = None
    last_publish_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    elapsed_seconds: float = 0.0
    errors: list[dict[str, Any]] = Field(default_factory=list)


class StreamStopResponse(BaseModel):
    """Response after stopping a stream."""

    success: bool = True
    message: str = "Stream stopped"
    total_published: int = 0
    total_failed: int = 0
