"""
Service-specific clients for ASLP services.

Each client provides a typed interface to a specific service's REST API.
"""

from typing import Any, Dict, Optional, List
from shared_sdk.clients.base import BaseClient, ClientConfig
from shared_sdk.constants import DefaultTimeout, DefaultPorts
from shared_sdk.logger import get_logger

logger = get_logger("service_clients")


class BrokerClient(BaseClient):
    """Client for Message Broker service."""

    def __init__(self, base_url: str = "", timeout: float = DefaultTimeout.MEDIUM):
        url = base_url or f"http://localhost:{DefaultPorts.MESSAGE_BROKER}"
        config = ClientConfig(base_url=url, timeout=timeout)
        super().__init__(config)

    async def get_queue_info(self, queue_name: str = "stream_queue") -> Dict[str, Any]:
        """Get queue information."""
        return await self.get(f"/api/v1/queue/{queue_name}")

    async def get_exchange_info(self, exchange_name: str = "stream_exchange") -> Dict[str, Any]:
        """Get exchange information."""
        return await self.get(f"/api/v1/exchange/{exchange_name}")

    async def get_connection_info(self) -> Dict[str, Any]:
        """Get active connections."""
        return await self.get("/api/v1/connections")

    async def publish_message(self, exchange: str, routing_key: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Publish a message to the broker."""
        return await self.post(
            "/api/v1/publish",
            json={
                "exchange": exchange,
                "routing_key": routing_key,
                "message": message,
            },
        )


class StateStoreClient(BaseClient):
    """Client for State Store service."""

    def __init__(self, base_url: str = "", timeout: float = DefaultTimeout.MEDIUM):
        url = base_url or f"http://localhost:{DefaultPorts.STATE_STORE}"
        config = ClientConfig(base_url=url, timeout=timeout)
        super().__init__(config)

    async def save_state(
        self,
        model_name: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        version: int = 1,
    ) -> Dict[str, Any]:
        """Save model state."""
        return await self.post(
            "/api/v1/state",
            json={
                "model_name": model_name,
                "state": state,
                "metadata": metadata or {},
                "version": version,
            },
        )

    async def load_state(self, model_name: str, version: Optional[int] = None) -> Dict[str, Any]:
        """Load model state."""
        params = {}
        if version:
            params["version"] = version
        return await self.get(f"/api/v1/state/{model_name}", params=params)

    async def list_states(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """List available states."""
        params = {}
        if model_name:
            params["model_name"] = model_name
        return await self.get("/api/v1/state", params=params)

    async def delete_state(self, model_name: str, version: Optional[int] = None) -> Dict[str, Any]:
        """Delete model state."""
        params = {}
        if version:
            params["version"] = version
        return await self.delete(f"/api/v1/state/{model_name}", params=params)

    async def get_metadata(self, model_name: str) -> Dict[str, Any]:
        """Get state metadata."""
        return await self.get(f"/api/v1/state/{model_name}/metadata")


class StorageClient(BaseClient):
    """Client for Storage Layer service."""

    def __init__(self, base_url: str = "", timeout: float = DefaultTimeout.MEDIUM):
        url = base_url or f"http://localhost:{DefaultPorts.STORAGE_LAYER}"
        config = ClientConfig(base_url=url, timeout=timeout)
        super().__init__(config)

    async def save(
        self,
        collection: str,
        document: Dict[str, Any],
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a document to a collection."""
        if document_id:
            return await self.put(f"/api/v1/storage/{collection}/{document_id}", json=document)
        return await self.post(f"/api/v1/storage/{collection}", json=document)

    async def find(
        self,
        collection: str,
        query: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Find documents in a collection."""
        params = {"limit": limit, "offset": offset}
        if query:
            params["query"] = query
        if sort:
            params["sort"] = sort
        return await self.get(f"/api/v1/storage/{collection}", params=params)

    async def find_one(self, collection: str, document_id: str) -> Dict[str, Any]:
        """Find a single document by ID."""
        return await self.get(f"/api/v1/storage/{collection}/{document_id}")

    async def update(
        self,
        collection: str,
        document_id: str,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a document."""
        return await self.put(f"/api/v1/storage/{collection}/{document_id}", json=document)

    async def delete(self, collection: str, document_id: str) -> Dict[str, Any]:
        """Delete a document."""
        return await self.delete(f"/api/v1/storage/{collection}/{document_id}")

    async def count(self, collection: str, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Count documents in a collection."""
        params = {}
        if query:
            params["query"] = query
        return await self.get(f"/api/v1/storage/{collection}/count", params=params)

    async def list_collections(self) -> Dict[str, Any]:
        """List all collections."""
        return await self.get("/api/v1/storage/collections")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return await self.get("/api/v1/storage/statistics")


class OnlineMLClient(BaseClient):
    """Client for Online ML Engine service."""

    def __init__(self, base_url: str = "", timeout: float = DefaultTimeout.MEDIUM):
        url = base_url or f"http://localhost:{DefaultPorts.ONLINE_ML_ENGINE}"
        config = ClientConfig(base_url=url, timeout=timeout)
        super().__init__(config)

    async def get_model_info(self) -> Dict[str, Any]:
        """Get current model information."""
        return await self.get("/api/v1/model")

    async def get_metrics(self, window: int = 1000) -> Dict[str, Any]:
        """Get model metrics."""
        return await self.get("/api/v1/metrics", params={"window": window})

    async def get_predictions(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get prediction history."""
        return await self.get("/api/v1/predictions", params={"limit": limit, "offset": offset})

    async def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        return await self.get("/api/v1/learning")

    async def trigger_save_state(self) -> Dict[str, Any]:
        """Trigger manual state save."""
        return await self.post("/api/v1/state/save")

    async def trigger_load_state(self, model_name: str, version: Optional[int] = None) -> Dict[str, Any]:
        """Trigger manual state load."""
        params = {}
        if version:
            params["version"] = version
        return await self.post(f"/api/v1/state/load/{model_name}", params=params)

    async def switch_model(self, model_name: str) -> Dict[str, Any]:
        """Switch active model."""
        return await self.post("/api/v1/model/switch", json={"model_name": model_name})


class StreamingPreprocessingClient(BaseClient):
    """Client for Streaming Preprocessing Service."""

    def __init__(self, base_url: str = "", timeout: float = DefaultTimeout.MEDIUM):
        url = base_url or f"http://localhost:{DefaultPorts.STREAMING_PREPROCESSING}"
        config = ClientConfig(base_url=url, timeout=timeout)
        super().__init__(config)

    async def start_streaming(self) -> Dict[str, Any]:
        """Start data streaming."""
        return await self.post("/api/v1/stream/start")

    async def stop_streaming(self) -> Dict[str, Any]:
        """Stop data streaming."""
        return await self.post("/api/v1/stream/stop")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get preprocessing statistics."""
        return await self.get("/api/v1/statistics")

    async def get_current_config(self) -> Dict[str, Any]:
        """Get current preprocessing configuration."""
        return await self.get("/api/v1/config")

    async def reload_config(self) -> Dict[str, Any]:
        """Reload preprocessing configuration."""
        return await self.post("/api/v1/config/reload")


# Convenience factory functions
async def create_broker_client(base_url: str = "") -> BrokerClient:
    """Create and initialize broker client."""
    client = BrokerClient(base_url)
    await client._get_client()  # Force connection
    return client


async def create_state_store_client(base_url: str = "") -> StateStoreClient:
    """Create and initialize state store client."""
    client = StateStoreClient(base_url)
    await client._get_client()
    return client


async def create_storage_client(base_url: str = "") -> StorageClient:
    """Create and initialize storage client."""
    client = StorageClient(base_url)
    await client._get_client()
    return client


async def create_online_ml_client(base_url: str = "") -> OnlineMLClient:
    """Create and initialize online ML client."""
    client = OnlineMLClient(base_url)
    await client._get_client()
    return client


async def create_streaming_client(base_url: str = "") -> StreamingPreprocessingClient:
    """Create and initialize streaming client."""
    client = StreamingPreprocessingClient(base_url)
    await client._get_client()
    return client


__all__ = [
    "BrokerClient",
    "StateStoreClient",
    "StorageClient",
    "OnlineMLClient",
    "StreamingPreprocessingClient",
    "create_broker_client",
    "create_state_store_client",
    "create_storage_client",
    "create_online_ml_client",
    "create_streaming_client",
]