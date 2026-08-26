"""Business logic for the Configuration Service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories import ConfigurationRepository


class ConfigurationService:
    """Encapsulates configuration read/write and reload behavior."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ConfigurationRepository(session)
        self.cache: dict[str, dict[str, Any]] = {}
        self.last_reload_at: datetime | None = None

    async def seed_defaults(self) -> int:
        """Insert default platform configs if they are missing."""
        inserted = 0
        for service_name, config_data in settings.DEFAULT_CONFIGS.items():
            existing = await self.repository.get(service_name)
            if existing is None:
                await self.repository.upsert(service_name, config_data, description="Default configuration")
                inserted += 1
        await self.session.commit()
        await self.refresh_cache()
        return inserted

    async def refresh_cache(self) -> None:
        """Reload all configurations into memory."""
        configs = await self.repository.list_all()
        self.cache = {config.service_name: config.to_dict() for config in configs}
        self.last_reload_at = datetime.utcnow()

    async def get_all(self) -> list[dict[str, Any]]:
        if not self.cache:
            await self.refresh_cache()
        return list(self.cache.values())

    async def get_one(self, service_name: str) -> dict[str, Any] | None:
        if not self.cache:
            await self.refresh_cache()
        return self.cache.get(service_name)

    async def upsert(self, service_name: str, config_data: dict[str, Any], description: str | None = None) -> dict[str, Any]:
        config = await self.repository.upsert(service_name, config_data, description)
        await self.session.commit()
        await self.refresh_cache()
        return config.to_dict()

    async def reload(self, service_name: str | None = None, force: bool = False) -> dict[str, Any]:
        if force or not self.cache:
            await self.refresh_cache()

        if service_name:
            config = await self.get_one(service_name)
            return {
                "reloaded": config is not None,
                "service_name": service_name,
                "total_loaded": 1 if config else 0,
                "message": (
                    f"Configuration reloaded for {service_name}"
                    if config
                    else f"Configuration not found for {service_name}"
                ),
            }

        await self.refresh_cache()
        return {
            "reloaded": True,
            "service_name": None,
            "total_loaded": len(self.cache),
            "message": "All configurations reloaded successfully.",
        }

    async def delete(self, service_name: str) -> bool:
        deleted = await self.repository.delete(service_name)
        if deleted:
            await self.session.commit()
            await self.refresh_cache()
        return deleted

    async def stats(self) -> dict[str, Any]:
        if not self.cache:
            await self.refresh_cache()
        return {
            "service": settings.SERVICE_NAME,
            "status": "running",
            "version": settings.SERVICE_VERSION,
            "uptime_seconds": 0.0,
            "total_configs": len(self.cache),
            "cached_configs": len(self.cache),
            "database_status": "connected",
            "last_reload_at": self.last_reload_at,
        }
