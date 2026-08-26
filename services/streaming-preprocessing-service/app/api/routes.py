"""API routes for Streaming Preprocessing Service — Milestone 3 with full preprocessing pipeline."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status as http_status

from app.schemas import (
    BootstrapResponse,
    ConfigReloadResponse,
    HealthResponse,
    ServiceStatus,
    StreamStartRequest,
    StreamStatusResponse,
    StreamStatisticsResponse,
    StreamStopResponse,
)
from app.services.streaming_service import StreamingOrchestrator

router = APIRouter()

# ------------------------------------------------------------------
# Singleton orchestrator (lazy — first call creates it)
# ------------------------------------------------------------------

_orchestrator: StreamingOrchestrator | None = None
_config_service = None


async def get_config_service():
    """Singleton runtime configuration service."""
    global _config_service
    if _config_service is None:
        from app.services.config_service import StreamingConfigService
        _config_service = StreamingConfigService()
    return _config_service


async def get_orchestrator() -> StreamingOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = StreamingOrchestrator(config_service=await get_config_service())
    return _orchestrator


# ------------------------------------------------------------------
# Configuration endpoints (Milestone 2)
# ------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
async def health(config_service=Depends(get_config_service)):
    """Check service health and configuration status."""
    status = config_service.status()
    return HealthResponse(config_loaded=status["config_loaded"])


@router.get("/status", response_model=ServiceStatus)
async def status(config_service=Depends(get_config_service)):
    """Get detailed service status including preprocessing pipeline."""
    return ServiceStatus(**config_service.status())


@router.post("/config/reload", response_model=ConfigReloadResponse)
async def reload_config(config_service=Depends(get_config_service)):
    """Reload preprocessing configuration from Configuration Service."""
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
async def bootstrap(config_service=Depends(get_config_service)):
    """Bootstrap service with default configuration."""
    config = await config_service.load()
    return BootstrapResponse(success=True, message="Config loaded", config=config)


# ------------------------------------------------------------------
# Streaming endpoints (Milestone 3) with preprocessing pipeline
# ------------------------------------------------------------------

@router.post("/stream/start", response_model=StreamStatusResponse)
async def stream_start(
    request: StreamStartRequest,
    orch: StreamingOrchestrator = Depends(get_orchestrator),
):
    """Start streaming data from a CSV source to the Message Broker.

    Initializes preprocessing pipeline (validation -> transformation -> feature engineering)
    and starts the background streaming task.
    """
    await orch.start(request)
    return orch.status()


@router.post("/stream/stop", response_model=StreamStopResponse)
async def stream_stop(
    orch: StreamingOrchestrator = Depends(get_orchestrator),
):
    """Stop the currently running stream and cleanup."""
    return await orch.stop()


@router.get("/stream/status", response_model=StreamStatusResponse)
async def stream_status(
    orch: StreamingOrchestrator = Depends(get_orchestrator),
):
    """Check whether a stream is running and get its progress."""
    return orch.status()


@router.get("/statistics", response_model=StreamStatisticsResponse)
async def stream_statistics(
    orch: StreamingOrchestrator = Depends(get_orchestrator),
):
    """Get detailed statistics from the streaming session and preprocessing pipeline."""
    return orch.statistics()


# ------------------------------------------------------------------
# Preprocessing pipeline administration endpoints (NEW)
# ------------------------------------------------------------------

@router.get("/pipeline/validation", response_model=dict)
async def get_validation_stats(
    orch: StreamingOrchestrator = Depends(get_orchestrator),
):
    """Get validation pipeline statistics (schema, missing values, duplicates)."""
    if orch._validation_pipeline:
        return orch._validation_pipeline.get_stats()
    return {"error": "Validation pipeline not enabled"}


@router.get("/pipeline/transformation", response_model=dict)
async def get_transformation_stats(
    orch: StreamingOrchestrator = Depends(get_orchestrator),
):
    """Get transformation pipeline statistics (type conversion, cleaning, encoding, normalization)."""
    if orch._transformation_pipeline:
        return orch._transformation_pipeline.get_stats()
    return {"error": "Transformation pipeline not enabled"}


@router.get("/pipeline/features", response_model=dict)
async def get_feature_pipeline_stats(
    orch: StreamingOrchestrator = Depends(get_orchestrator),
):
    """Get feature engineering pipeline statistics."""
    if orch._feature_pipeline:
        return orch._feature_pipeline.get_stats()
    return {"error": "Feature pipeline not enabled"}


@router.get("/pipeline/stats", response_model=dict)
async def get_full_pipeline_stats(
    orch: StreamingOrchestrator = Depends(get_orchestrator),
):
    """Get complete preprocessing pipeline statistics across all stages."""
    stats = {"total_rows": 0, "rejected_rows": 0, "success_rate": 0.0, "stages": {}}

    if orch._validation_pipeline:
        stats["stages"]["validation"] = orch._validation_pipeline.get_stats()
        stats["total_rows"] += stats["stages"]["validation"].get("total_rows", 0)
        stats["rejected_rows"] += stats["stages"]["validation"].get("rejected_rows", 0)

    if orch._transformation_pipeline:
        stats["stages"]["transformation"] = orch._transformation_pipeline.get_stats()
        stats["total_rows"] += stats["stages"]["transformation"].get("total_rows", 0)
        stats["rejected_rows"] += stats["stages"]["transformation"].get("rejected_rows", 0)

    if orch._feature_pipeline:
        stats["stages"]["feature_engineering"] = orch._feature_pipeline.get_stats()
        stats["total_rows"] += stats["stages"]["feature_engineering"].get("total_rows", 0)
        stats["rejected_rows"] += stats["stages"]["feature_engineering"].get("rejected_rows", 0)

    if stats["total_rows"] > 0:
        stats["success_rate"] = (stats["total_rows"] - stats["rejected_rows"]) / stats["total_rows"]

    return stats


@router.get("/pipeline/session/errors", response_model=dict)
async def get_session_errors(
    orch: StreamingOrchestrator = Depends(get_orchestrator),
):
    """Get preprocessing errors from current streaming session."""
    if orch._session and orch._session.errors:
        return {
            "total_errors": len(orch._session.errors),
            "recent_errors": orch._session.errors[-10:],
        }
    return {"total_errors": 0, "recent_errors": []}


@router.post("/pipeline/reset", status_code=http_status.HTTP_204_NO_CONTENT)
async def reset_pipelines(
    orch: StreamingOrchestrator = Depends(get_orchestrator),
):
    """Reset all preprocessing pipelines and clear accumulated state."""
    if orch._validation_pipeline:
        orch._validation_pipeline.reset()
    if orch._transformation_pipeline:
        orch._transformation_pipeline.reset()
    if orch._feature_pipeline:
        orch._feature_pipeline.reset()
    if orch._session:
        orch._session.errors.clear()
    return None
