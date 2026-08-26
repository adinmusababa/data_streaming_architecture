"""Repository layer for the Configuration Service."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConfigurationModel


class ConfigurationRepository:
    """Persistence helper for service configurations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[ConfigurationModel]:
        result = await self.session.execute(select(ConfigurationModel).order_by(ConfigurationModel.service_name))
        return list(result.scalars().all())

    async def get(self, service_name: str) -> ConfigurationModel | None:
        result = await self.session.execute(
            select(ConfigurationModel).where(ConfigurationModel.service_name == service_name)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        service_name: str,
        config_data: dict[str, Any],
        description: str | None = None,
    ) -> ConfigurationModel:
        config = await self.get(service_name)
        if config is None:
            config = ConfigurationModel(
                service_name=service_name,
                config_data=config_data,
                description=description,
                version=1,
            )
            self.session.add(config)
        else:
            config.config_data = config_data
            config.version += 1
            config.description = description if description is not None else config.description
        await self.session.flush()
        return config

    async def delete(self, service_name: str) -> bool:
        result = await self.session.execute(
            delete(ConfigurationModel).where(ConfigurationModel.service_name == service_name)
        )
        return result.rowcount > 0
