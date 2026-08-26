"""
Broker Publisher — publishes StreamMessage payloads to the Message Broker.

Uses the shared-sdk BrokerClient which wraps a BaseClient (httpx) with
circuit breaker, retry, and structured logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shared_sdk.clients import BrokerClient
from shared_sdk.constants import DefaultPorts
from shared_sdk.logger import get_logger
from shared_sdk.models import StreamMessage

logger = get_logger("broker_publisher")


@dataclass
class PublishStats:
    """Cumulative publish statistics."""

    total_attempted: int = 0
    total_succeeded: int = 0
    total_failed: int = 0
    last_publish_at: datetime | None = None
    first_publish_at: datetime | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_attempted == 0:
            return 1.0
        return self.total_succeeded / self.total_attempted

    def record_success(self) -> None:
        now = datetime.utcnow()
        self.total_attempted += 1
        self.total_succeeded += 1
        self.last_publish_at = now
        if self.first_publish_at is None:
            self.first_publish_at = now

    def record_failure(self, error: str) -> None:
        now = datetime.utcnow()
        self.total_attempted += 1
        self.total_failed += 1
        self.last_publish_at = now
        if self.first_publish_at is None:
            self.first_publish_at = now
        self.errors.append({"time": now.isoformat(), "error": error})
        # Keep only last 100 errors in memory
        if len(self.errors) > 100:
            self.errors.pop(0)


class BrokerPublisher:
    """Publishes StreamMessage objects to the configured broker exchange/queue.

    Args:
        broker_url:  Base URL of the Message Broker service.
                      Defaults to the standard port (8003).
        exchange:    Exchange name on the broker.
        routing_key: Routing key (queue binding).
    """

    def __init__(
        self,
        broker_url: str = "",
        exchange: str = "stream_exchange",
        routing_key: str = "stream_data",
    ) -> None:
        self._exchange = exchange
        self._routing_key = routing_key
        self._client = BrokerClient(
            base_url=broker_url or f"http://localhost:{DefaultPorts.MESSAGE_BROKER}",
        )
        self._stats = PublishStats()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def statistics(self) -> PublishStats:
        """Cumulative publish statistics."""
        return self._stats

    def _build_payload(self, message: StreamMessage) -> dict[str, Any]:
        """Convert a StreamMessage model to the broker payload dict."""
        return {
            "stream_id": message.stream_id,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
            "source": message.source,
            "event_type": message.event_type.value if message.event_type else "data_point",
            "data": message.data,
            "metadata": message.metadata,
        }

    async def publish(self, message: StreamMessage) -> bool:
        """Publish a single StreamMessage to the broker.

        Returns True on success, False on failure.
        """
        payload = self._build_payload(message)
        try:
            await self._client.publish_message(
                exchange=self._exchange,
                routing_key=self._routing_key,
                message=payload,
            )
            self._stats.record_success()
            logger.debug(
                "Message published",
                stream_id=message.stream_id,
                source=message.source,
            )
            return True
        except Exception as exc:
            self._stats.record_failure(str(exc))
            logger.error(
                "Publish failed",
                stream_id=message.stream_id,
                error=str(exc),
            )
            return False

    async def publish_batch(self, messages: list[StreamMessage]) -> tuple[int, int]:
        """Publish a batch of messages.

        Returns (succeeded, failed) counts.
        """
        succeeded = 0
        failed = 0
        for msg in messages:
            ok = await self.publish(msg)
            if ok:
                succeeded += 1
            else:
                failed += 1
        logger.info(
            "Batch published",
            total=len(messages),
            succeeded=succeeded,
            failed=failed,
        )
        return succeeded, failed

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.close()
        logger.info(
            "Publisher closed",
            total_published=self._stats.total_succeeded,
            total_failed=self._stats.total_failed,
        )
