"""
Utility functions for ASLP services.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar, Optional
from functools import wraps
import asyncio
from shared_sdk.logger import get_logger
from shared_sdk.constants import DefaultTimeout

T = TypeVar("T")
logger = get_logger("utils")


def generate_uuid() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


def now_utc() -> datetime:
    """Get current UTC datetime with timezone."""
    return datetime.now(timezone.utc)


def json_dumps(obj: Any, **kwargs) -> str:
    """Serialize to JSON with default handlers."""
    return json.dumps(obj, default=str, ensure_ascii=False, **kwargs)


def json_loads(s: str) -> Any:
    """Deserialize JSON."""
    return json.loads(s)


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        exceptions: Exception types to catch and retry
        on_retry: Optional callback(exception, attempt) on each retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                        if on_retry:
                            on_retry(e, attempt)
                        logger.warning(
                            f"Retry {attempt}/{max_attempts} for {func.__name__} after {delay:.1f}s: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                        if on_retry:
                            on_retry(e, attempt)
                        logger.warning(
                            f"Retry {attempt}/{max_attempts} for {func.__name__} after {delay:.1f}s: {e}"
                        )
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        async with self._lock:
            if self.state == "open":
                import time
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half-open"
                else:
                    raise ServiceUnavailableException("circuit_breaker", "Circuit breaker is open")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            async with self._lock:
                self.failure_count = 0
                self.state = "closed"
            return result
        except self.expected_exception as e:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
            raise


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length."""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def safe_get(d: dict, *keys, default: Any = None) -> Any:
    """Safely get nested dictionary value."""
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    return d


def merge_dicts(*dicts: dict) -> dict:
    """Merge multiple dictionaries (shallow)."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result