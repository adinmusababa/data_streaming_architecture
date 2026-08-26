"""
Streaming Orchestrator — coordinates the CSV → JSON → Broker pipeline.

Reads data from a source (CSV), converts each row into the standard
StreamMessage payload, and publishes it to the Message Broker via the
BrokerPublisher.

The orchestrator runs as an asyncio background task so HTTP endpoints
can start / stop it without blocking.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from shared_sdk.logger import get_logger
from shared_sdk.models import StreamMessage, EventType
from shared_sdk.utils import generate_uuid

from app.reader import CsvReader
from app.publisher import BrokerPublisher
from app.schemas.streaming import (
    StreamStartRequest,
    StreamStatusResponse,
    StreamStatisticsResponse,
    StreamStopResponse,
)
from app.validators import ValidationPipeline
from app.transformers import TransformationPipeline
from app.features import FeaturePipeline

logger = get_logger("streaming_orchestrator")


@dataclass
class StreamSession:
    """Holds state for one active streaming session."""

    source_path: str = ""
    source_type: str = "csv"
    batch_size: int = 10
    polling_interval: float = 1.0
    publish_topic: str = "stream_data"
    started_at: Optional[datetime] = None
    total_batches: int = 0
    total_rows: int = 0
    total_published: int = 0
    total_failed: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    _task: asyncio.Task | None = None


class StreamingOrchestrator:
    """Lifecycle manager for a single CSV→JSON→Broker streaming pipeline.

    Usage::

        orch = StreamingOrchestrator()
        await orch.start(StreamStartRequest(source_path="data.csv"))
        ...
        status = orch.status()
        stats = orch.statistics()
        await orch.stop()
    """

    def __init__(
        self,
        validation_pipeline: ValidationPipeline | None = None,
        transformation_pipeline: TransformationPipeline | None = None,
        feature_pipeline: FeaturePipeline | None = None,
        config_service: Any | None = None,
    ) -> None:
        self._session = StreamSession()
        self._publisher: BrokerPublisher | None = None

        # Preprocessing pipelines (built from config service on start())
        self._validation_pipeline = validation_pipeline
        self._transformation_pipeline = transformation_pipeline
        self._feature_pipeline = feature_pipeline
        self._config_service = config_service

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self, request: StreamStartRequest) -> None:
        """Start a streaming session in a background task.

        If a session is already running it will be stopped first.
        """
        if self.is_running:
            logger.warning("Stream already running — stopping first")
            await self.stop()

        self._session = StreamSession(
            source_path=request.source_path,
            source_type=request.source_type,
            batch_size=request.batch_size,
            polling_interval=request.polling_interval,
            publish_topic=request.publish_topic,
            started_at=datetime.utcnow(),
        )
        # One publisher per session — pick a fresh topic/exchange from config
        # when a full broker service exists; for now we publish to the
        # default exchange via BrokerClient.
        self._publisher = BrokerPublisher(routing_key=request.publish_topic)

        # Initialize pipelines with config from config service if available
        await self._initialize_pipelines(request)

        self._session._task = asyncio.create_task(self._run())
        logger.info(
            "Stream started",
            source=request.source_path,
            batch_size=request.batch_size,
        )

    async def _initialize_pipelines(self, request: StreamStartRequest) -> None:
        """Build preprocessing pipelines from the Configuration Service.

        Falls back to local defaults when the configuration service is
        unreachable, so a stream can always start.
        """
        if self._config_service is not None:
            try:
                runtime_config = await self._config_service.load()
            except Exception as exc:
                logger.warning("Config service load failed — using defaults", error=str(exc))
                runtime_config = {}
        else:
            runtime_config = {}

        # Session parameters follow the Configuration Service unless the
        # caller explicitly overrode them in the request body.
        explicit = getattr(request, "model_fields_set", set())
        overrides = {
            "source_type": str,
            "batch_size": int,
            "polling_interval": float,
            "publish_topic": str,
        }
        for key, caster in overrides.items():
            if key not in explicit and key in runtime_config:
                setattr(self._session, key, caster(runtime_config[key]))

        enabled_stages = set(runtime_config.get("preprocessing_pipeline", ["validation", "transformation"]))
        self._validation_pipeline = (
            ValidationPipeline.from_config(runtime_config.get("validation", {}))
            if "validation" in enabled_stages
            else None
        )
        self._transformation_pipeline = (
            TransformationPipeline.from_config(runtime_config.get("transformation", {}))
            if "transformation" in enabled_stages or "cleaning" in enabled_stages
            else None
        )
        self._feature_pipeline = FeaturePipeline.from_config(runtime_config.get("features", {}))

        logger.info(
            "Preprocessing pipelines initialized",
            validation=self._validation_pipeline is not None,
            transformation=self._transformation_pipeline is not None,
            feature_engineering=self._feature_pipeline is not None,
        )

    async def stop(self) -> StreamStopResponse:
        """Stop the running stream and return a summary."""
        if not self.is_running:
            return StreamStopResponse(
                message="No stream is currently running",
                total_published=self._session.total_published,
                total_failed=self._session.total_failed,
            )

        # Cancel the background task
        if self._session._task and not self._session._task.done():
            self._session._task.cancel()
            try:
                await self._session._task
            except asyncio.CancelledError:
                pass

        # Close the publisher
        if self._publisher:
            await self._publisher.close()

        resp = StreamStopResponse(
            success=True,
            message="Stream stopped",
            total_published=self._session.total_published,
            total_failed=self._session.total_failed,
        )
        logger.info(
            "Stream stopped",
            published=resp.total_published,
            failed=resp.total_failed,
        )
        return resp

    # ------------------------------------------------------------------
    # Status / statistics
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return (
            self._session._task is not None
            and not self._session._task.done()
        )

    def status(self) -> StreamStatusResponse:
        """Lightweight current-status snapshot."""
        elapsed = 0.0
        if self._session.started_at:
            elapsed = (datetime.utcnow() - self._session.started_at).total_seconds()
        pub_stats = self._publisher.statistics if self._publisher else None
        return StreamStatusResponse(
            is_running=self.is_running,
            source_path=self._session.source_path or None,
            source_type=self._session.source_type,
            total_rows_read=self._session.total_rows,
            total_rows_estimated=0,  # Updated during run
            total_published=pub_stats.total_succeeded if pub_stats else 0,
            total_failed=pub_stats.total_failed if pub_stats else 0,
            started_at=self._session.started_at,
            elapsed_seconds=elapsed,
        )

    def statistics(self) -> StreamStatisticsResponse:
        """Full session statistics."""
        elapsed = 0.0
        if self._session.started_at:
            ended = datetime.utcnow()
            elapsed = (ended - self._session.started_at).total_seconds()
        pub_stats = self._publisher.statistics if self._publisher else None
        return StreamStatisticsResponse(
            total_batches=self._session.total_batches,
            total_rows=self._session.total_rows,
            total_published=pub_stats.total_succeeded if pub_stats else 0,
            total_failed=pub_stats.total_failed if pub_stats else 0,
            success_rate=pub_stats.success_rate if pub_stats else 1.0,
            first_publish_at=pub_stats.first_publish_at if pub_stats else None,
            last_publish_at=pub_stats.last_publish_at if pub_stats else None,
            started_at=self._session.started_at,
            elapsed_seconds=elapsed,
            errors=pub_stats.errors if pub_stats else [],
        )

    # ------------------------------------------------------------------
    # Internal — the background loop
    # ------------------------------------------------------------------

    async def _run(self) -> None:
        """Background loop: read CSV → validate → transform → feature engineer → build StreamMessage → publish.

        Full preprocessing pipeline:
        1. Read data from source
        2. Validation (schema, missing values, duplicates)
        3. Transformation (type conversion, cleaning, encoding, normalization)
        4. Feature Engineering (derived features, window features, aggregations)
        5. Build StreamMessage payload
        6. Publish to Message Broker
        """
        reader: CsvReader | None = None
        try:
            reader = CsvReader(self._session.source_path)
            reader.open()
            logger.info("Data source opened", source=self._session.source_path)

            while self.is_running:
                rows = await reader.read_batch(self._session.batch_size)
                if not rows:
                    logger.info("End of CSV file reached — stream complete")
                    break

                processed_rows = []
                validation_results = []
                for idx, row in enumerate(rows):
                    current_row = dict(row)

                    # Stage 1: Validation
                    if self._validation_pipeline:
                        val_result = self._validation_pipeline.validate(current_row, idx)
                        if not val_result.is_valid:
                            logger.warning(
                                "Row rejected by validation",
                                row_index=idx,
                                errors=val_result.all_errors,
                            )
                            self._session.errors.append({
                                "row_index": idx,
                                "stage": "validation",
                                "errors": val_result.all_errors,
                            })
                            continue
                        current_row = val_result.final_row

                    # Stage 2: Transformation
                    if self._transformation_pipeline:
                        transform_result = self._transformation_pipeline.transform(current_row, idx)
                        if not transform_result.is_valid:
                            logger.warning(
                                "Row rejected by transformation",
                                row_index=idx,
                                errors=transform_result.all_errors,
                            )
                            self._session.errors.append({
                                "row_index": idx,
                                "stage": "transformation",
                                "errors": transform_result.all_errors,
                            })
                            continue
                        current_row = transform_result.final_row

                    # Stage 3: Feature Engineering
                    if self._feature_pipeline:
                        feature_result = self._feature_pipeline.process(current_row, idx)
                        if not feature_result.is_valid:
                            logger.warning(
                                "Row rejected by feature engineering",
                                row_index=idx,
                                errors=feature_result.all_errors,
                            )
                            self._session.errors.append({
                                "row_index": idx,
                                "stage": "feature_engineering",
                                "errors": feature_result.all_errors,
                            })
                            continue
                        current_row = feature_result.final_row

                    processed_rows.append(current_row)

                if not processed_rows:
                    logger.info("All rows in batch were rejected by preprocessing")
                    self._session.total_batches += 1
                    await asyncio.sleep(self._session.polling_interval)
                    continue

                # Build messages from processed rows
                messages = self._rows_to_messages(processed_rows)
                self._session.total_rows += len(processed_rows)
                self._session.total_batches += 1

                succeeded, failed = await self._publisher.publish_batch(messages)
                self._session.total_published += succeeded
                self._session.total_failed += failed

                logger.info(
                    "Batch processed",
                    batch=self._session.total_batches,
                    rows_original=len(rows),
                    rows_accepted=len(processed_rows),
                    rows_rejected=len(rows) - len(processed_rows),
                    published=succeeded,
                    failed=failed,
                )

                # Wait before next batch
                if rows:
                    await asyncio.sleep(self._session.polling_interval)

        except asyncio.CancelledError:
            logger.info("Stream task cancelled")
            raise
        except FileNotFoundError:
            logger.error("CSV file not found", path=self._session.source_path)
            self._session.errors.append({"error": f"File not found: {self._session.source_path}"})
        except Exception as exc:
            logger.exception("Stream task error", error=str(exc))
            self._session.errors.append({"error": str(exc)})
        finally:
            if reader:
                reader.close()
                logger.info("Data reader closed")
            if self._validation_pipeline:
                logger.info("Validation stats", stats=self._validation_pipeline.get_stats())
            if self._transformation_pipeline:
                logger.info("Transformation stats", stats=self._transformation_pipeline.get_stats())
            if self._feature_pipeline:
                logger.info("Feature pipeline stats", stats=self._feature_pipeline.get_stats())
            if self._publisher:
                await self._publisher.close()

    # ------------------------------------------------------------------
    # Payload building
    # ------------------------------------------------------------------

    def _rows_to_messages(self, rows: list[dict[str, Any]]) -> list[StreamMessage]:
        """Convert processed CSV row dicts to StreamMessage list."""
        stream_id = generate_uuid()
        messages: list[StreamMessage] = []
        for row in rows:
            # Separate known metadata fields from the actual data payload
            known_meta = {"sensor_id", "timestamp", "status"}
            data = {k: v for k, v in row.items() if k not in known_meta}
            meta = {k: v for k, v in row.items() if k in known_meta}

            msg = StreamMessage(
                stream_id=stream_id,
                source=self._session.source_path,
                event_type=EventType.DATA_POINT,
                data=data,
                metadata={
                    **meta,
                    "batch": self._session.total_batches,
                    "source_type": self._session.source_type,
                    "publish_topic": self._session.publish_topic,
                    "has_validation": self._validation_pipeline is not None,
                    "has_transformation": self._transformation_pipeline is not None,
                    "has_feature_engineering": self._feature_pipeline is not None,
                },
            )
            messages.append(msg)
        return messages
