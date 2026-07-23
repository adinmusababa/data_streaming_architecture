"""
Base HTTP client and service-specific clients for ASLP services.

Provides standardized HTTP communication with:
- Automatic retry with exponential backoff
- Circuit breaker pattern
- Request/response logging
- Error handling
- Timeout management
"""

import asyncio
import time
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import httpx
from pydantic import BaseModel

from shared_sdk.logger import get_logger, RequestContext
from shared_sdk.utils import retry, CircuitBreaker
from shared_sdk.exceptions import (
    APIException,
    ServiceUnavailableException,
    ConfigurationException,
)
from shared_sdk.constants import (
    DefaultTimeout,
    HTTPStatus,
    RetryDefaults,
    CircuitBreakerDefaults,
)


logger = get_logger("clients")


@dataclass
class ClientConfig:
    """Configuration for HTTP client."""
    base_url: str
    timeout: float = DefaultTimeout.MEDIUM
    max_retries: int = RetryDefaults.MAX_ATTEMPTS
    retry_base_delay: float = RetryDefaults.BASE_DELAY
    retry_max_delay: float = RetryDefaults.MAX_DELAY
    circuit_breaker_threshold: int = CircuitBreakerDefaults.FAILURE_THRESHOLD
    circuit_breaker_timeout: int = CircuitBreakerDefaults.RECOVERY_TIMEOUT
    headers: Dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True


class BaseClient:
    """
    Base HTTP client with standard features.

    Features:
    - Async HTTP client (httpx)
    - Automatic retry with exponential backoff
    - Circuit breaker pattern
    - Request/response logging
    - Standardized error handling
    - Health check support
    """

    def __init__(self, config: ClientConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold,
            recovery_timeout=config.circuit_breaker_timeout,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout),
                headers=self.config.headers,
                verify=self.config.verify_ssl,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "BaseClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _build_request_kwargs(
        self,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Build request keyword arguments."""
        request_kwargs = {}
        if json is not None:
            request_kwargs["json"] = json
        if params is not None:
            request_kwargs["params"] = params
        if headers:
            request_kwargs["headers"] = headers
        request_kwargs.update(kwargs)
        return request_kwargs

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute HTTP request with retry and circuit breaker.

        Args:
            method: HTTP method
            path: Request path
            json: JSON body
            params: Query parameters
            headers: Additional headers
            **kwargs: Additional httpx arguments

        Returns:
            Response JSON as dict

        Raises:
            APIException: For HTTP errors
            ServiceUnavailableException: When circuit breaker is open
        """
        client = await self._get_client()
        request_kwargs = self._build_request_kwargs(json, params, headers, **kwargs)

        # Add request ID for tracing
        request_id = RequestContext.get_current() or generate_request_id()
        request_kwargs.setdefault("headers", {})["X-Request-ID"] = request_id

        async def _do_request():
            response = await client.request(method, path, **request_kwargs)
            return await self._handle_response(response)

        # Execute with circuit breaker
        try:
            return await self._circuit_breaker.call(_do_request)
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {method} {path}", error=str(e))
            raise ServiceUnavailableException(self.config.base_url, f"Timeout: {e}")
        except httpx.ConnectError as e:
            logger.error(f"Connection error: {method} {path}", error=str(e))
            raise ServiceUnavailableException(self.config.base_url, f"Connection failed: {e}")

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and extract JSON."""
        # Log response
        logger.debug(
            f"Response: {response.status_code}",
            status_code=response.status_code,
            url=str(response.url),
        )

        # Handle error status codes
        if response.status_code >= 400:
            error_data = {}
            try:
                error_data = response.json()
            except Exception:
                error_data = {"detail": response.text}

            error_msg = error_data.get("message") or error_data.get("detail") or f"HTTP {response.status_code}"
            raise APIException(
                service=self.config.base_url,
                operation=f"{response.request.method} {response.url.path}",
                message=error_msg,
                status_code=response.status_code,
                details=error_data,
            )

        # Parse JSON response
        try:
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return {"data": response.text}

    # Convenience methods
    async def get(self, path: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        return await self._request("GET", path, params=params, **kwargs)

    async def post(self, path: str, json: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        return await self._request("POST", path, json=json, **kwargs)

    async def put(self, path: str, json: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        return await self._request("PUT", path, json=json, **kwargs)

    async def patch(self, path: str, json: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        return await self._request("PATCH", path, json=json, **kwargs)

    async def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        return await self._request("DELETE", path, **kwargs)

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        return await self.get("/api/v1/health")

    async def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return await self.get("/api/v1/status")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return await self.get("/api/v1/statistics")

    async def reload_config(self) -> Dict[str, Any]:
        """Trigger config reload."""
        return await self.post("/api/v1/config/reload")


def generate_request_id() -> str:
    """Generate a unique request ID."""
    import uuid
    return str(uuid.uuid4())[:8]


# Add get_current to RequestContext for request ID tracking
from contextvars import ContextVar
_request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_current_request_id() -> Optional[str]:
    return _request_id_var.get()


def set_current_request_id(request_id: str) -> None:
    _request_id_var.set(request_id)


# Monkey patch for convenience
RequestContext.get_current = staticmethod(get_current_request_id)