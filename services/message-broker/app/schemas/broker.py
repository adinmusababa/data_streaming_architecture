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


class SubscribeRequest(BaseModel):
    """Register a persistent consumer group on a queue (SAS-07 workflow)."""

    queue: str = Field(default="stream_queue")
    group_id: str = Field(..., min_length=1, description="Consumer group name")
    prefetch_count: int = Field(default=100, ge=1, le=10_000)


class SubscribeResponse(BaseModel):
    subscribed: bool
    queue: str
    group_id: str


class FetchRequest(BaseModel):
    """Receive messages without committing their offsets."""

    queue: str = Field(default="stream_queue")
    group_id: str = Field(..., min_length=1)
    max_messages: int = Field(default=10, ge=1, le=1000)
    timeout_ms: int = Field(default=1000, ge=0, le=60_000)


class FetchResponse(BaseModel):
    queue: str
    group_id: str
    messages: list[dict[str, Any]]
    count: int


class AckRequest(BaseModel):
    """Acknowledgement — commit the offset of a delivered message."""

    queue: str = Field(default="stream_queue")
    group_id: str = Field(..., min_length=1)
    delivery_tag: str = Field(..., min_length=1, description="<topic>:<partition>:<offset>")


class AckResponse(BaseModel):
    acknowledged: bool
    delivery_tag: str


class NackRequest(BaseModel):
    """Negative acknowledgement — requeue or dead-letter the message."""

    queue: str = Field(default="stream_queue")
    group_id: str = Field(..., min_length=1)
    delivery_tag: str = Field(..., min_length=1)
    requeue: bool = Field(default=False, description="True: redeliver. False: route to DLQ.")
    reason: str = Field(default="", description="Why the message was rejected")


class NackResponse(BaseModel):
    nacked: bool
    delivery_tag: str
    requeued: bool
    dlq_topic: str | None = None


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
