"""
Structured logging for ASLP services.

Provides consistent log formatting, context propagation, and service identification.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
from enum import Enum
import traceback

from shared_sdk.constants import LogLevel, ServiceName


# Context variables for request/service tracking
_request_context: ContextVar[Optional["RequestContext"]] = ContextVar("request_context", default=None)
_service_context: ContextVar[Optional["ServiceContext"]] = ContextVar("service_context", default=None)


class LogLevel(str, Enum):
    """Log levels matching standard Python logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class RequestContext:
    """Request-scoped context for logging."""
    request_id: str = ""
    method: str = ""
    path: str = ""
    client_ip: str = ""
    user_agent: str = ""
    start_time: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ServiceContext:
    """Service-scoped context for logging."""
    service_name: str = ""
    service_version: str = "1.0.0"
    instance_id: str = ""
    environment: str = "development"
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class JSONFormatter(logging.Formatter):
    """JSON log formatter with context enrichment."""

    def __init__(self, service_name: str = "", include_trace: bool = True):
        super().__init__()
        self.service_name = service_name
        self.include_trace = include_trace

    def format(self, record: logging.LogRecord) -> str:
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
        }

        # Add service context
        svc_ctx = _service_context.get()
        if svc_ctx:
            log_entry["service_context"] = svc_ctx.to_dict()

        # Add request context
        req_ctx = _request_context.get()
        if req_ctx:
            log_entry["request_context"] = req_ctx.to_dict()
            # Add duration if available
            if req_ctx.start_time:
                log_entry["duration_ms"] = round((datetime.utcnow().timestamp() - req_ctx.start_time) * 1000, 2)

        # Add extra fields from record
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "name", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "getMessage"
            }
        }
        if extra_fields:
            log_entry["extra"] = extra_fields

        # Add exception info
        if record.exc_info and self.include_trace:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class SystemLogger:
    """
    Main logger class for ASLP services.

    Features:
    - JSON structured logging
    - Automatic context propagation
    - Service identification
    - Request tracking
    """

    def __init__(
        self,
        name: str,
        service_name: str = "",
        level: Union[int, str] = logging.INFO,
        json_format: bool = True,
        include_trace: bool = True,
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.service_name = service_name

        # Clear existing handlers
        self.logger.handlers.clear()

        # Create handler
        handler = logging.StreamHandler(sys.stdout)

        if json_format:
            handler.setFormatter(JSONFormatter(service_name, include_trace))
        else:
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )

        self.logger.addHandler(handler)
        self.logger.propagate = False

    def _log(self, level: int, message: str, **kwargs) -> None:
        """Internal log method with extra fields."""
        self.logger.log(level, message, extra=kwargs)

    def debug(self, message: str, **kwargs) -> None:
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self._log(logging.ERROR, message, exc_info=True, **kwargs)

    # Convenience methods for common patterns
    def request_start(self, request_id: str, method: str, path: str, **extra) -> None:
        """Log request start."""
        ctx = RequestContext(
            request_id=request_id,
            method=method,
            path=path,
            start_time=datetime.utcnow().timestamp(),
            extra=extra,
        )
        _request_context.set(ctx)
        self.info("Request started", request_id=request_id, method=method, path=path, **extra)

    def request_end(self, status_code: int, **extra) -> None:
        """Log request completion."""
        ctx = _request_context.get()
        duration = 0
        if ctx and ctx.start_time:
            duration = round((datetime.utcnow().timestamp() - ctx.start_time) * 1000, 2)
        self.info(
            "Request completed",
            request_id=ctx.request_id if ctx else "",
            status_code=status_code,
            duration_ms=duration,
            **extra,
        )
        _request_context.set(None)

    def request_error(self, error: Exception, **extra) -> None:
        """Log request error."""
        ctx = _request_context.get()
        self.error(
            "Request failed",
            request_id=ctx.request_id if ctx else "",
            error_type=type(error).__name__,
            error_message=str(error),
            **extra,
        )
        _request_context.set(None)


# Global logger registry
_loggers: Dict[str, SystemLogger] = {}


def get_logger(name: str, service_name: str = "", level: Union[int, str] = logging.INFO) -> SystemLogger:
    """Get or create a logger for the given name."""
    key = f"{service_name}:{name}" if service_name else name
    if key not in _loggers:
        _loggers[key] = SystemLogger(name, service_name, level)
    return _loggers[key]


def set_global_level(level: Union[int, str]) -> None:
    """Set log level for all registered loggers."""
    for logger in _loggers.values():
        logger.logger.setLevel(level)


def set_service_context(context: ServiceContext) -> None:
    """Set global service context."""
    _service_context.set(context)


def get_service_context() -> Optional[ServiceContext]:
    """Get current service context."""
    return _service_context.get()


def set_request_context(context: RequestContext) -> None:
    """Set current request context."""
    _request_context.set(context)


def get_request_context() -> Optional[RequestContext]:
    """Get current request context."""
    return _request_context.get()


class RequestLogger:
    """Logger specialized for HTTP request/response logging."""

    def __init__(self, logger: SystemLogger):
        self.logger = logger

    def log_request(self, method: str, path: str, request_id: str, **extra) -> None:
        self.logger.request_start(request_id, method, path, **extra)

    def log_response(self, status_code: int, **extra) -> None:
        self.logger.request_end(status_code, **extra)

    def log_error(self, error: Exception, **extra) -> None:
        self.logger.request_error(error, **extra)


class ErrorLogger:
    """Logger specialized for error tracking."""

    def __init__(self, logger: SystemLogger):
        self.logger = logger

    def log_error(self, error: Exception, context: str = "", **extra) -> None:
        self.logger.error(
            f"Error in {context}: {error}",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            **extra,
        )

    def log_validation_error(self, field: str, value: Any, constraint: str, **extra) -> None:
        self.logger.warning(
            f"Validation failed: {field}={value} (constraint: {constraint})",
            validation_field=field,
            validation_value=str(value)[:100],
            validation_constraint=constraint,
            **extra,
        )

    def log_external_service_error(
        self,
        service: str,
        operation: str,
        error: Exception,
        **extra
    ) -> None:
        self.logger.error(
            f"External service error: {service}.{operation}",
            external_service=service,
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            **extra,
        )


# Pre-configured loggers for common use cases
def create_service_logger(service_name: str, level: Union[int, str] = logging.INFO) -> SystemLogger:
    """Create a logger configured for a specific service."""
    return get_logger(f"aslp.{service_name}", service_name, level)


# Module-level convenience loggers
_system_logger = create_service_logger("system")
_request_logger = RequestLogger(_system_logger)
_error_logger = ErrorLogger(_system_logger)

__all__ = [
    "SystemLogger",
    "RequestLogger",
    "ErrorLogger",
    "RequestContext",
    "ServiceContext",
    "get_logger",
    "set_global_level",
    "set_service_context",
    "get_service_context",
    "set_request_context",
    "get_request_context",
    "create_service_logger",
    "LogLevel",
    "JSONFormatter",
]