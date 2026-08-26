"""Configuration bootstrap for Streaming Preprocessing Service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared_sdk.configuration import ConfigLoader
from shared_sdk.logger import get_logger

from app.core.config import settings

logger = get_logger("streaming-preprocessing-service")


class StreamingConfigService:
    """Loads runtime config from the Configuration Service."""

    def __init__(self) -> None:
        self.loader = ConfigLoader(
            service_name=settings.SERVICE_NAME,
            config_service_url=settings.CONFIG_SERVICE_URL,
            defaults=settings.DEFAULT_STREAMING_CONFIG,
            cache_ttl=30,
        )
        self.runtime_config: dict[str, Any] = dict(settings.DEFAULT_STREAMING_CONFIG)
        self.last_reload_at: datetime | None = None
        self.config_loaded: bool = False

    async def load(self) -> dict[str, Any]:
        config = await self.loader.refresh()
        self.runtime_config = self._normalize(config)
        self.last_reload_at = datetime.utcnow()
        self.config_loaded = True
        logger.info("Streaming config loaded", config=self.runtime_config)
        return self.runtime_config

    async def reload(self) -> dict[str, Any]:
        config = await self.loader.refresh()
        self.runtime_config = self._normalize(config)
        self.last_reload_at = datetime.utcnow()
        self.config_loaded = True
        logger.info("Streaming config reloaded", config=self.runtime_config)
        return self.runtime_config

    def status(self) -> dict[str, Any]:
        return {
            "service": settings.SERVICE_NAME,
            "status": "running",
            "config_loaded": self.config_loaded,
            "config_source": settings.CONFIG_SERVICE_URL,
            "last_reload_at": self.last_reload_at,
        }

    def _normalize(self, config: dict[str, Any]) -> dict[str, Any]:
        merged = dict(settings.DEFAULT_STREAMING_CONFIG)
        merged.update(config or {})
        return merged
