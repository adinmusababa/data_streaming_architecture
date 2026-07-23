"""
Standard response models for all ASLP services.
"""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Base response model with common fields."""
    success: bool
    message: str
    data: Optional[T] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}


class SuccessResponse(BaseResponse[T]):
    """Standard success response."""
    success: bool = True
    message: str = "Operation completed successfully."


class ErrorResponse(BaseResponse[T]):
    """Standard error response."""
    success: bool = False
    message: str = "An error occurred."
    errors: Optional[list] = None


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field details."""
    errors: list = Field(default_factory=list)

    @classmethod
    def from_pydantic_errors(cls, errors: list, message: str = "Validation failed") -> "ValidationErrorResponse":
        """Create from Pydantic validation errors."""
        formatted_errors = [
            {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"], "type": err["type"]}
            for err in errors
        ]
        return cls(message=message, errors=formatted_errors)


class PaginatedResponse(BaseResponse[list[T]]):
    """Paginated list response."""
    page: int = 1
    size: int = 20
    total: int = 0
    total_pages: int = 0

    @classmethod
    def create(cls, items: list[T], page: int, size: int, total: int) -> "PaginatedResponse[T]":
        """Create paginated response from items."""
        total_pages = (total + size - 1) // size if total > 0 else 0
        return cls(
            data=items,
            page=page,
            size=size,
            total=total,
            total_pages=total_pages,
            message=f"Retrieved {len(items)} items (page {page}/{total_pages})",
        )