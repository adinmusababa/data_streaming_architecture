"""Pydantic schemas for Message Broker REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PublishRequest(BaseModel):
    """Standard publish contract used by shared_sdk BrokerClient."""

    exchange: str = Field(..., description="Target exchange name")
    routing_key: str = Field(..., description="Routing key (topic binding)")
    message: dict[str, Any] = Field(..., description="Message payload")


class PublishResponse(BaseModel):
    published: bool
    exchange: str
    routing_key: str
    queue: str
    partition: int | None = None
    offset: int | None = None


class ConsumeRequest(BaseModel):
    queue: str = Field(default="stream_queue")
    max_messages: int = Field(default=10, ge=1, le=1000)
    timeout_ms: int = Field(default=1000, ge=0, le=60_000)


class ConsumeResponse(BaseModel):
    queue: str
    messages: list[dict[str, Any]]
    count: int


class QueueInfoResponse(BaseModel):
    name: str
    message_count: int
    exists: bool


class ExchangeInfoResponse(BaseModel):
    name: str
    bindings: list[str]
    exists: bool


class ConnectionsResponse(BaseModel):
    active_publishers: int
    active_consumers: int
    kafka_bootstrap: str
    kafka_connected: bool


class HealthResponse(BaseModel):
    status: str
    version: str
    kafka: str
    config_loaded: bool


class StatusResponse(BaseModel):
    service: str
    status: str
    config_loaded: bool
    config_source: str
    last_reload_at: datetime | None = None
    uptime_seconds: float
    total_published: int
    total_consumed: int
    total_failed: int
    errors: list[dict[str, Any]] = Field(default_factory=list)


class StatisticsResponse(BaseModel):
    total_message: int
    total_publish: int
    total_consume: int
    total_failed: int
    queue_size: int
    processing_rate_per_sec: float
    last_message_at: datetime | None = None


class ConfigReloadResponse(BaseModel):
    reloaded: bool
    message: str
    exchange: str
    queue: str
    routing_key: str
