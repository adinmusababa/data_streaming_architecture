"""REST API routes for the Message Broker Service.

Publish/consume contract matches shared_sdk.clients.BrokerClient:
    POST /api/v1/publish           {exchange, routing_key, message}
    GET  /api/v1/queue/{name}
    GET  /api/v1/exchange/{name}
    GET  /api/v1/connections
"""

from __future__ import annotations

from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Query

from app.broker import KafkaBackend, topic_for
from app.core.config import settings
from app.schemas import (
    ConfigReloadResponse,
    ConsumeRequest,
    ConsumeResponse,
    ConnectionsResponse,
    ExchangeInfoResponse,
    HealthResponse,
    PublishRequest,
    PublishResponse,
    QueueInfoResponse,
    StatisticsResponse,
    StatusResponse,
)
from app.services.broker_service import BrokerConfigService

router = APIRouter()

_backend: KafkaBackend | None = None
_config_service: BrokerConfigService | None = None


def get_config_service() -> BrokerConfigService:
    global _config_service
    if _config_service is None:
        _config_service = BrokerConfigService()
    return _config_service


async def get_backend() -> KafkaBackend:
    global _backend
    if _backend is None:
        config = get_config_service().runtime_config
        host = str(config.get("host", "localhost"))
        port = int(config.get("port", 9092))
        _backend = KafkaBackend(bootstrap_servers=f"{host}:{port}")
    return _backend


async def init_broker() -> None:
    """Start config load and Kafka connection. Called from app lifespan."""
    config_service = get_config_service()
    await config_service.load()
    backend = await get_backend()
    try:
        await backend.start()
        queue = str(config_service.runtime_config.get("queue", "stream_queue"))
        exchange = str(config_service.runtime_config.get("exchange", "stream_exchange"))
        routing_key = str(config_service.runtime_config.get("routing_key", "stream_data"))
        await backend.ensure_topic(topic_for(exchange, routing_key))
        await backend.ensure_topic(queue)
    except Exception as exc:
        # Degrade gracefully: REST endpoints report kafka=down until it recovers.
        from shared_sdk.logger import get_logger

        get_logger("message-broker").error("Kafka unavailable on startup", error=str(exc))


async def shutdown_broker() -> None:
    if _backend is not None:
        await _backend.stop()


# ------------------------------------------------------------------
# Health & status (SAS-07 section 13)
# ------------------------------------------------------------------


@router.get("/health", response_model=HealthResponse)
@router.get("/api/v1/health", response_model=HealthResponse, include_in_schema=False)
async def health(
    config_service: BrokerConfigService = Depends(get_config_service),
    backend: KafkaBackend = Depends(get_backend),
):
    return HealthResponse(
        status="healthy" if backend.connected else "degraded",
        version=settings.SERVICE_VERSION,
        kafka="connected" if backend.connected else "disconnected",
        config_loaded=config_service.config_loaded,
    )


@router.get("/status", response_model=StatusResponse)
@router.get("/api/v1/status", response_model=StatusResponse, include_in_schema=False)
async def status_endpoint(
    config_service: BrokerConfigService = Depends(get_config_service),
    backend: KafkaBackend = Depends(get_backend),
):
    s = config_service.status()
    stats = backend.stats
    return StatusResponse(
        **s,
        uptime_seconds=round(monotonic() - stats.started_at, 3),
        total_published=stats.total_publish,
        total_consumed=stats.total_consume,
        total_failed=stats.total_failed,
        errors=stats.errors[-10:],
    )


@router.post("/config/reload", response_model=ConfigReloadResponse)
@router.post("/api/v1/config/reload", response_model=ConfigReloadResponse, include_in_schema=False)
async def reload_config(config_service: BrokerConfigService = Depends(get_config_service)):
    await config_service.reload()
    cfg = config_service.runtime_config
    return ConfigReloadResponse(
        reloaded=True,
        message="Configuration reloaded successfully.",
        exchange=str(cfg.get("exchange")),
        queue=str(cfg.get("queue")),
        routing_key=str(cfg.get("routing_key")),
    )


# ------------------------------------------------------------------
# Publish / consume — contract used by shared_sdk BrokerClient
# ------------------------------------------------------------------


@router.post("/api/v1/publish", response_model=PublishResponse)
async def publish(payload: PublishRequest, backend: KafkaBackend = Depends(get_backend)):
    try:
        meta = await backend.publish(
            exchange=payload.exchange,
            routing_key=payload.routing_key,
            message=payload.message,
            retry_count=int(get_config_service().runtime_config.get("retry_count", 3)),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return PublishResponse(
        published=True,
        exchange=payload.exchange,
        routing_key=payload.routing_key,
        queue=topic_for(payload.exchange, payload.routing_key),
        partition=meta["partition"],
        offset=meta["offset"],
    )


@router.post("/api/v1/consume", response_model=ConsumeResponse)
async def consume(request: ConsumeRequest, backend: KafkaBackend = Depends(get_backend)):
    try:
        messages = await backend.consume(
            queue=request.queue,
            max_messages=request.max_messages,
            timeout_ms=request.timeout_ms,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Consume failed: {exc}")
    return ConsumeResponse(queue=request.queue, messages=messages, count=len(messages))


# ------------------------------------------------------------------
# Monitoring endpoints (SAS-07 sections 13-14)
# ------------------------------------------------------------------


@router.get("/queue", response_model=list[QueueInfoResponse])
@router.get("/api/v1/queue", response_model=list[QueueInfoResponse], include_in_schema=False)
async def list_queues(backend: KafkaBackend = Depends(get_backend)):
    topics = await backend.list_topics()
    visible = [t for t in topics if "__consumer_offsets" not in t]
    result = []
    for topic in visible:
        size = await backend.queue_size(topic)
        result.append(QueueInfoResponse(name=topic, message_count=size or 0, exists=True))
    return result


@router.get("/api/v1/queue/{queue_name}", response_model=QueueInfoResponse)
async def queue_info(queue_name: str, backend: KafkaBackend = Depends(get_backend)):
    size = await backend.queue_size(queue_name)
    if size is None:
        raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' not found")
    return QueueInfoResponse(name=queue_name, message_count=size, exists=True)


@router.get("/api/v1/exchange/{exchange_name}", response_model=ExchangeInfoResponse)
async def exchange_info(exchange_name: str, backend: KafkaBackend = Depends(get_backend)):
    bindings = await backend.topic_bindings(exchange_name)
    return ExchangeInfoResponse(name=exchange_name, bindings=bindings, exists=bool(bindings))


@router.get("/connections", response_model=ConnectionsResponse)
@router.get("/api/v1/connections", response_model=ConnectionsResponse, include_in_schema=False)
async def connections(backend: KafkaBackend = Depends(get_backend)):
    return ConnectionsResponse(
        active_publishers=1 if backend.connected else 0,
        active_consumers=0,
        kafka_bootstrap=backend.bootstrap_servers,
        kafka_connected=backend.connected,
    )


@router.get("/statistics", response_model=StatisticsResponse)
@router.get("/api/v1/statistics", response_model=StatisticsResponse, include_in_schema=False)
async def statistics(
    config_service: BrokerConfigService = Depends(get_config_service),
    backend: KafkaBackend = Depends(get_backend),
):
    stats = backend.stats
    queue_name = str(config_service.runtime_config.get("queue", "stream_queue"))
    size = await backend.queue_size(queue_name)
    return StatisticsResponse(
        total_message=stats.total_message,
        total_publish=stats.total_publish,
        total_consume=stats.total_consume,
        total_failed=stats.total_failed,
        queue_size=size or 0,
        processing_rate_per_sec=stats.processing_rate_per_sec,
        last_message_at=stats.last_message_at,
    )
