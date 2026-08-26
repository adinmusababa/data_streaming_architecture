"""
Configuration client for Configuration Service.

Provides dynamic configuration loading with caching and change notification.
"""

import asyncio
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime

from shared_sdk.clients.base import BaseClient, ClientConfig
from shared_sdk.logger import get_logger
from shared_sdk.utils import retry
from shared_sdk.exceptions import ConfigurationException
from shared_sdk.constants import DefaultTimeout, DefaultPorts

logger = get_logger("config")


@dataclass
class ConfigCache:
    """In-memory configuration cache with TTL."""
    data: Dict[str, Any] = field(default_factory=dict)
    etag: Optional[str] = None
    last_updated: Optional[datetime] = None
    ttl_seconds: int = 60

    def is_valid(self) -> bool:
        if not self.data or not self.last_updated:
            return False
        age = (datetime.utcnow() - self.last_updated).total_seconds()
        return age < self.ttl_seconds

    def get(self, key: str, default: Any = None) -> Any:
        if not self.is_valid():
            return default
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if not self.is_valid():
            self.data = {}
        self.data[key] = value
        self.last_updated = datetime.utcnow()


class ConfigLoader:
    """
    Dynamic configuration loader with caching and polling.

    Features:
    - Fetches configuration from Configuration Service
    - In-memory caching with TTL
    - Background polling for changes
    - Change callbacks
    - Fallback to defaults
    """

    def __init__(
        self,
        service_name: str,
        config_service_url: str = "",
        cache_ttl: int = 60,
        poll_interval: int = 30,
        defaults: Optional[Dict[str, Any]] = None,
    ):
        self.service_name = service_name
        self.config_service_url = config_service_url or f"http://localhost:{DefaultPorts.CONFIGURATION}"
        self.cache = ConfigCache(ttl_seconds=cache_ttl)
        self.poll_interval = poll_interval
        self.defaults = defaults or {}
        self._client: Optional[BaseClient] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._running = False

    async def _get_client(self) -> BaseClient:
        if self._client is None:
            config = ClientConfig(
                base_url=self.config_service_url,
                timeout=DefaultTimeout.MEDIUM,
            )
            self._client = BaseClient(config)
        return self._client

    async def start(self) -> None:
        """Start configuration polling."""
        if self._running:
            return
        self._running = True
        # Initial load
        await self.refresh()
        # Start polling
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info(f"Config loader started for {self.service_name}")

    async def stop(self) -> None:
        """Stop configuration polling."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        if self._client:
            await self._client.close()
        logger.info(f"Config loader stopped for {self.service_name}")

    async def _poll_loop(self) -> None:
        """Background polling loop."""
        while self._running:
            try:
                await asyncio.sleep(self.poll_interval)
                if self._running:
                    await self.refresh()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Config poll error: {e}")

    async def refresh(self) -> Dict[str, Any]:
        """Fetch latest configuration from service."""
        client = await self._get_client()
        try:
            response = await client.get(f"/api/v1/config/{self.service_name}")
            config_data = response.get("data", {})
            self.cache.data = config_data
            self.cache.last_updated = datetime.utcnow()
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(config_data)
                except Exception as e:
                    logger.error(f"Config callback error: {e}")
            logger.info(f"Config refreshed for {self.service_name}")
            return config_data
        except Exception as e:
            logger.warning(f"Config refresh failed, using cache: {e}")
            return self.cache.data

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value (from cache)."""
        value = self.cache.get(key)
        if value is not None:
            return value
        return self.defaults.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration (from cache)."""
        if self.cache.is_valid():
            return self.cache.data.copy()
        return self.defaults.copy()

    def on_change(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for configuration changes."""
        self._callbacks.append(callback)

    async def update_config(self, key: str, value: Any) -> Dict[str, Any]:
        """Update a configuration value on the service."""
        client = await self._get_client()
        response = await client.put(
            f"/api/v1/config/{self.service_name}",
            json={key: value},
        )
        await self.refresh()  # Refresh local cache
        return response


class ConfigurationClient(BaseClient):
    """Client for Configuration Service operations."""

    def __init__(self, base_url: str = "", timeout: float = DefaultTimeout.MEDIUM):
        url = base_url or f"http://localhost:{DefaultPorts.CONFIGURATION}"
        config = ClientConfig(base_url=url, timeout=timeout)
        super().__init__(config)

    async def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service."""
        response = await self.get(f"/api/v1/config/{service_name}")
        return response.get("data", {})

    async def get_all_config(self) -> Dict[str, Any]:
        """Get all service configurations."""
        response = await self.get("/api/v1/config")
        return response.get("data", {})

    async def update_config(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update service configuration."""
        return await self.put(f"/api/v1/config/{service_name}", json=config)

    async def register_service(
        self,
        service_name: str,
        base_url: str,
        health_endpoint: str = "/api/v1/health",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register a service with the configuration service."""
        return await self.post(
            "/api/v1/services/register",
            json={
                "service_name": service_name,
                "base_url": base_url,
                "health_endpoint": health_endpoint,
                "metadata": metadata or {},
            },
        )

    async def list_services(self) -> Dict[str, Any]:
        """List all registered services."""
        return await self.get("/api/v1/services")

    async def get_service(self, service_name: str) -> Dict[str, Any]:
        """Get service registration info."""
        return await self.get(f"/api/v1/services/{service_name}")


async def load_service_config(
    service_name: str,
    config_service_url: str = "",
    defaults: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    One-time configuration load helper.

    Args:
        service_name: Name of the service
        config_service_url: Configuration service URL
        defaults: Default values if config unavailable

    Returns:
        Configuration dictionary
    """
    loader = ConfigLoader(service_name, config_service_url, defaults=defaults)
    try:
        return await loader.refresh()
    finally:
        await loader.stop()