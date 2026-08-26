"""
Standard exception hierarchy for ASLP services.
"""

from typing import Any, Optional
from shared_sdk.constants import HTTPStatus


class APIException(Exception):
    """Base exception for all API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        detail: Optional[Any] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or self.__class__.__name__

    def to_dict(self) -> dict:
        """Convert to dictionary for response."""
        return {
            "success": False,
            "message": self.message,
            "error_code": self.error_code,
            "detail": self.detail,
            "status_code": self.status_code,
        }


class ValidationException(APIException):
    """Raised when request validation fails."""

    def __init__(self, message: str = "Validation failed", detail: Any = None, errors: Optional[list] = None):
        super().__init__(message, HTTPStatus.UNPROCESSABLE_ENTITY, detail, "VALIDATION_ERROR")
        self.errors = errors or []


class ConfigurationException(APIException):
    """Raised when configuration is missing or invalid."""

    def __init__(self, message: str = "Configuration error", detail: Any = None):
        super().__init__(message, HTTPStatus.INTERNAL_SERVER_ERROR, detail, "CONFIGURATION_ERROR")


class StorageException(APIException):
    """Raised when storage operation fails."""

    def __init__(self, message: str = "Storage operation failed", detail: Any = None):
        super().__init__(message, HTTPStatus.INTERNAL_SERVER_ERROR, detail, "STORAGE_ERROR")


class StateException(APIException):
    """Raised when state store operation fails."""

    def __init__(self, message: str = "State operation failed", detail: Any = None):
        super().__init__(message, HTTPStatus.INTERNAL_SERVER_ERROR, detail, "STATE_ERROR")


class ServiceUnavailableException(APIException):
    """Raised when a dependent service is unavailable."""

    def __init__(self, service_name: str, message: Optional[str] = None, detail: Any = None):
        msg = message or f"Service '{service_name}' is unavailable"
        super().__init__(msg, HTTPStatus.SERVICE_UNAVAILABLE, detail, "SERVICE_UNAVAILABLE")
        self.service_name = service_name


class NotFoundException(APIException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: Any, detail: Any = None):
        super().__init__(
            f"{resource} not found: {identifier}",
            HTTPStatus.NOT_FOUND,
            detail,
            "NOT_FOUND",
        )
        self.resource = resource
        self.identifier = identifier


class ConflictException(APIException):
    """Raised when a resource conflict occurs."""

    def __init__(self, message: str = "Resource conflict", detail: Any = None):
        super().__init__(message, HTTPStatus.CONFLICT, detail, "CONFLICT")


class UnauthorizedException(APIException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Unauthorized", detail: Any = None):
        super().__init__(message, HTTPStatus.UNAUTHORIZED, detail, "UNAUTHORIZED")


class ForbiddenException(APIException):
    """Raised when access is forbidden."""

    def __init__(self, message: str = "Forbidden", detail: Any = None):
        super().__init__(message, HTTPStatus.FORBIDDEN, detail, "FORBIDDEN")