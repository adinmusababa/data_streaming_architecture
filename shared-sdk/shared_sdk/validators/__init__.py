"""
Validation utilities for ASLP services.
"""

from typing import Any, Callable, Optional
from pydantic import BaseModel, validator
from shared_sdk.exceptions import ValidationException


class BaseValidator:
    """Base validator class with common validation methods."""

    @staticmethod
    def required(value: Any, field_name: str) -> Any:
        """Validate required field."""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationException(f"{field_name} is required")
        return value

    @staticmethod
    def min_length(value: str, min_len: int, field_name: str) -> str:
        """Validate minimum string length."""
        if value and len(value) < min_len:
            raise ValidationException(f"{field_name} must be at least {min_len} characters")
        return value

    @staticmethod
    def max_length(value: str, max_len: int, field_name: str) -> str:
        """Validate maximum string length."""
        if value and len(value) > max_len:
            raise ValidationException(f"{field_name} must be at most {max_len} characters")
        return value

    @staticmethod
    def range_check_length(value: Any, min_val: Any, max_val: Any, field_name: str) -> Any:
        """Validate value is within range."""
        if value is not None and (value < min_val or value > max_val):
            raise ValidationException(f"{field_name} must be between {min_val} and {max_val}")
        return value

    @staticmethod
    def one_of(value: Any, allowed: list, field_name: str) -> Any:
        """Validate value is in allowed list."""
        if value is not None and value not in allowed:
            raise ValidationException(f"{field_name} must be one of: {allowed}")
        return value

    @staticmethod
    def pattern(value: str, regex: str, field_name: str) -> str:
        """Validate string matches regex pattern."""
        import re
        if value and not re.match(regex, value):
            raise ValidationException(f"{field_name} does not match required pattern")
        return value

    @staticmethod
    def email(value: str, field_name: str = "email") -> str:
        """Validate email format."""
        return BaseValidator.pattern(value, r"^[^@]+@[^@]+\.[^@]+$", field_name)

    @staticmethod
    def url(value: str, field_name: str = "url") -> str:
        """Validate URL format."""
        return BaseValidator.pattern(value, r"^https?://.+", field_name)


def validate_model(model_class: type[BaseModel], data: dict) -> BaseModel:
    """Validate data against Pydantic model."""
    try:
        return model_class(**data)
    except Exception as e:
        raise ValidationException("Validation failed", detail=str(e), errors=getattr(e, "errors", []))


# Common validator functions for use with Pydantic
def required_validator(field_name: str):
    """Create a required field validator."""
    def validator_func(cls, v):
        return BaseValidator.required(v, field_name)
    return validator_func


def range_validator(min_val: Any, max_val: Any, field_name: str):
    """Create a range validator."""
    def validator_func(cls, v):
        return BaseValidator.range(v, min_val, max_val, field_name)
    return validator_func


def one_of_validator(allowed: list, field_name: str):
    """Create a one-of validator."""
    def validator_func(cls, v):
        return BaseValidator.one_of(v, allowed, field_name)
    return validator_func


def pattern_validator(regex: str, field_name: str):
    """Create a pattern validator."""
    def validator_func(cls, v):
        return BaseValidator.pattern(v, regex, field_name)
    return validator_func