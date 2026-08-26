"""
Type Converter - Data type conversion for preprocessing pipeline.

Converts string values to appropriate types (int, float, bool, datetime).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from shared_sdk.logger import get_logger

logger = get_logger("type_converter")


class TargetType(str, Enum):
    """Target data types for conversion."""

    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    DATETIME = "datetime"
    STRING = "str"
    AUTO = "auto"  # Infer type from value


@dataclass
class TypeConversionResult:
    """Result of type conversion for a row."""

    is_valid: bool
    row_index: int
    original_row: dict[str, Any]
    converted_row: dict[str, Any] | None = None
    converted_fields: dict[str, str] = field(default_factory=dict)  # field -> target_type
    errors: list[dict[str, Any]] = field(default_factory=list)
    converted_at: datetime = field(default_factory=datetime.utcnow)


class TypeConverter:
    """
    Converts field values to specified target types.

    Supports explicit type mapping and automatic type inference.
    """

    def __init__(
        self,
        type_mapping: dict[str, TargetType] | None = None,
        auto_infer: bool = True,
        datetime_formats: list[str] | None = None,
        boolean_true_values: list[str] | None = None,
        boolean_false_values: list[str] | None = None,
        fail_on_error: bool = False,
    ) -> None:
        """
        Initialize type converter.

        Args:
            type_mapping: field_name -> TargetType mapping
            auto_infer: Automatically infer types for unmapped fields
            datetime_formats: List of datetime format strings to try
            boolean_true_values: Strings that map to True
            boolean_false_values: Strings that map to False
            fail_on_error: If True, raise on conversion error; else set field to None
        """
        self.type_mapping = type_mapping or {}
        self.auto_infer = auto_infer
        self.datetime_formats = datetime_formats or [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]
        self.boolean_true_values = set(boolean_true_values or ["true", "1", "yes", "y", "t", "on"])
        self.boolean_false_values = set(boolean_false_values or ["false", "0", "no", "n", "f", "off"])
        self.fail_on_error = fail_on_error

        self._stats = {
            "total_rows": 0,
            "converted_rows": 0,
            "failed_rows": 0,
            "conversions_by_type": {},
            "errors_by_field": {},
        }

    def convert(self, row: dict[str, Any], row_index: int = 0) -> TypeConversionResult:
        """
        Convert field values to target types.

        Returns TypeConversionResult with converted row or errors.
        """
        self._stats["total_rows"] += 1
        converted_row = dict(row)
        converted_fields = {}
        errors = []

        for field, value in row.items():
            if value is None:
                continue

            # Determine target type
            target_type = self.type_mapping.get(field)
            if target_type is None and self.auto_infer:
                target_type = self._infer_type(value)
            elif target_type is None:
                continue  # No conversion needed

            # Perform conversion
            try:
                converted = self._convert_value(value, target_type)
                if converted is not None:
                    converted_row[field] = converted
                    converted_fields[field] = target_type.value
                    self._stats["conversions_by_type"][target_type.value] = \
                        self._stats["conversions_by_type"].get(target_type.value, 0) + 1
            except Exception as e:
                error_info = {"field": field, "error": str(e), "value": value, "target_type": target_type.value}
                errors.append(error_info)
                self._stats["errors_by_field"][field] = self._stats["errors_by_field"].get(field, 0) + 1

                if self.fail_on_error:
                    raise
                else:
                    # Keep original value or set to None
                    converted_row[field] = None

        is_valid = len(errors) == 0
        if is_valid:
            self._stats["converted_rows"] += 1
        else:
            self._stats["failed_rows"] += 1
            logger.warning("Type conversion failed", row_index=row_index, errors=errors)

        return TypeConversionResult(
            is_valid=is_valid,
            row_index=row_index,
            original_row=row,
            converted_row=converted_row if is_valid else None,
            converted_fields=converted_fields,
            errors=errors,
        )

    def _infer_type(self, value: Any) -> TargetType | None:
        """Infer target type from value."""
        if isinstance(value, bool):
            return TargetType.BOOLEAN
        if isinstance(value, int):
            return TargetType.INTEGER
        if isinstance(value, float):
            return TargetType.FLOAT
        if isinstance(value, str):
            # Try to infer from string
            if self._looks_like_int(value):
                return TargetType.INTEGER
            if self._looks_like_float(value):
                return TargetType.FLOAT
            if self._looks_like_bool(value):
                return TargetType.BOOLEAN
            if self._looks_like_datetime(value):
                return TargetType.DATETIME
        return None

    def _looks_like_int(self, value: str) -> bool:
        """Check if string looks like integer."""
        try:
            int(value)
            return True
        except ValueError:
            return False

    def _looks_like_float(self, value: str) -> bool:
        """Check if string looks like float."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _looks_like_bool(self, value: str) -> bool:
        """Check if string looks like boolean."""
        return value.lower() in self.boolean_true_values or value.lower() in self.boolean_false_values

    def _looks_like_datetime(self, value: str) -> bool:
        """Check if string looks like datetime."""
        for fmt in self.datetime_formats:
            try:
                datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
        return False

    def _convert_value(self, value: Any, target_type: TargetType) -> Any:
        """Convert a single value to target type."""
        if value is None:
            return None

        if target_type == TargetType.INTEGER:
            if isinstance(value, bool):
                return int(value)
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                return int(float(value))  # Handle "1.0" -> 1
            raise ValueError(f"Cannot convert {type(value).__name__} to int")

        elif target_type == TargetType.FLOAT:
            if isinstance(value, (int, float, bool)):
                return float(value)
            if isinstance(value, str):
                return float(value)
            raise ValueError(f"Cannot convert {type(value).__name__} to float")

        elif target_type == TargetType.BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                lower = value.lower().strip()
                if lower in self.boolean_true_values:
                    return True
                if lower in self.boolean_false_values:
                    return False
                raise ValueError(f"Cannot convert '{value}' to boolean")
            raise ValueError(f"Cannot convert {type(value).__name__} to boolean")

        elif target_type == TargetType.DATETIME:
            if isinstance(value, datetime):
                return value
            if isinstance(value, (int, float)):
                # Unix timestamp
                return datetime.fromtimestamp(value)
            if isinstance(value, str):
                for fmt in self.datetime_formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"Cannot parse datetime: '{value}'")
            raise ValueError(f"Cannot convert {type(value).__name__} to datetime")

        elif target_type == TargetType.STRING:
            return str(value)

        raise ValueError(f"Unknown target type: {target_type}")

    def convert_batch(self, rows: list[dict[str, Any]]) -> list[TypeConversionResult]:
        """Convert a batch of rows."""
        return [self.convert(row, i) for i, row in enumerate(rows)]

    def get_valid_rows(self, results: list[TypeConversionResult]) -> list[dict[str, Any]]:
        """Extract valid converted rows."""
        return [r.converted_row for r in results if r.is_valid and r.converted_row]

    def get_stats(self) -> dict[str, Any]:
        """Get converter statistics."""
        stats = dict(self._stats)
        if stats["total_rows"] > 0:
            stats["success_rate"] = stats["converted_rows"] / stats["total_rows"]
        return stats

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            "total_rows": 0,
            "converted_rows": 0,
            "failed_rows": 0,
            "conversions_by_type": {},
            "errors_by_field": {},
        }

    def update_config(self, config: dict[str, Any]) -> None:
        """Update converter configuration."""
        if "type_mapping" in config:
            self.type_mapping = {k: TargetType(v) for k, v in config["type_mapping"].items()}
        if "auto_infer" in config:
            self.auto_infer = config["auto_infer"]
        if "datetime_formats" in config:
            self.datetime_formats = config["datetime_formats"]
        if "boolean_true_values" in config:
            self.boolean_true_values = set(config["boolean_true_values"])
        if "boolean_false_values" in config:
            self.boolean_false_values = set(config["boolean_false_values"])
        if "fail_on_error" in config:
            self.fail_on_error = config["fail_on_error"]
        logger.info("Type converter config updated", mapping_count=len(self.type_mapping))