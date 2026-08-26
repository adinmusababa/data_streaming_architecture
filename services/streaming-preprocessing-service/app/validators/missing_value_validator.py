"""
Missing Value Validator - Handles missing/null values in data rows.

Supports multiple strategies: reject, fill_constant, fill_mean, fill_median, fill_mode, fill_forward, fill_backward.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from shared_sdk.logger import get_logger

logger = get_logger("missing_value_validator")


class MissingValueStrategy(str, Enum):
    """Strategy for handling missing values."""

    REJECT = "reject"           # Reject row with missing values
    FILL_CONSTANT = "fill_constant"  # Fill with a constant value
    FILL_MEAN = "fill_mean"     # Fill with column mean (numeric)
    FILL_MEDIAN = "fill_median"       # Fill with column median (numeric)
    FILL_MODE = "fill_mode"     # Fill with column mode (most frequent)
    FILL_FORWARD = "fill_forward"     # Forward fill from previous row
    FILL_BACKWARD = "fill_backward"   # Backward fill from next row


@dataclass
class MissingValueResult:
    """Result of missing value validation for a single row."""

    is_valid: bool
    row_index: int
    processed_row: dict[str, Any] | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    filled_fields: list[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MissingValueStats:
    """Statistics for missing value handling."""

    total_rows: int = 0
    total_missing: int = 0
    total_filled: int = 0
    total_rejected: int = 0
    missing_by_field: dict[str, int] = field(default_factory=dict)
    filled_by_field: dict[str, int] = field(default_factory=dict)

    def record_missing(self, field: str) -> None:
        self.total_missing += 1
        self.missing_by_field[field] = self.missing_by_field.get(field, 0) + 1

    def record_filled(self, field: str) -> None:
        self.total_filled += 1
        self.filled_by_field[field] = self.filled_by_field.get(field, 0) + 1

    def record_rejected(self) -> None:
        self.total_rejected += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "total_missing": self.total_missing,
            "total_filled": self.total_filled,
            "total_rejected": self.total_rejected,
            "missing_by_field": self.missing_by_field,
            "filled_by_field": self.filled_by_field,
        }


class MissingValueValidator:
    """
    Validates and handles missing values in data rows.

    Configuration:
    - strategy: How to handle missing values
    - fill_values: Per-field constant values for FILL_CONSTANT strategy
    - required_fields: Fields that cannot be missing (even with fill strategies)
    - numeric_fields: Fields eligible for mean/median fill
    """

    def __init__(
        self,
        strategy: MissingValueStrategy = MissingValueStrategy.FILL_CONSTANT,
        fill_values: dict[str, Any] | None = None,
        required_fields: list[str] | None = None,
        numeric_fields: list[str] | None = None,
    ) -> None:
        self.strategy = strategy
        self.fill_values = fill_values or {}
        self.required_fields = set(required_fields or [])
        self.numeric_fields = set(numeric_fields or [])

        # Runtime statistics
        self._stats = MissingValueStats()

        # For mean/median/mode calculation
        self._column_values: dict[str, list[Any]] = {}
        self._column_stats: dict[str, dict[str, Any]] = {}
        self._prev_row: dict[str, Any] = {}

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = MissingValueStats()
        self._column_values = {}
        self._column_stats = {}
        self._prev_row = {}

    def get_stats(self) -> dict[str, Any]:
        """Get current statistics."""
        return self._stats.to_dict()

    def update_config(
        self,
        strategy: MissingValueStrategy | None = None,
        fill_values: dict[str, Any] | None = None,
        required_fields: list[str] | None = None,
        numeric_fields: list[str] | None = None,
    ) -> None:
        """Update configuration at runtime."""
        if strategy is not None:
            self.strategy = strategy
        if fill_values is not None:
            self.fill_values = fill_values
        if required_fields is not None:
            self.required_fields = set(required_fields)
        if numeric_fields is not None:
            self.numeric_fields = set(numeric_fields)
        logger.info("Missing value validator config updated", strategy=self.strategy.value)

    def _is_missing(self, value: Any) -> bool:
        """Check if a value is considered missing."""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        if isinstance(value, float) and value != value:  # NaN check
            return True
        return False

    def _collect_column_stats(self, row: dict[str, Any]) -> None:
        """Collect values for mean/median/mode calculation."""
        self._stats.total_rows += 1
        for field, value in row.items():
            if not self._is_missing(value):
                if field not in self._column_values:
                    self._column_values[field] = []
                self._column_values[field].append(value)

    def _compute_column_stats(self) -> None:
        """Compute mean, median, mode for numeric columns."""
        for field, values in self._column_values.items():
            if not values:
                continue

            # Try to convert to numeric for mean/median
            numeric_values = []
            for v in values:
                try:
                    numeric_values.append(float(v))
                except (ValueError, TypeError):
                    pass

            stats = {"count": len(values)}
            if numeric_values:
                sorted_vals = sorted(numeric_values)
                stats["mean"] = sum(numeric_values) / len(numeric_values)
                mid = len(sorted_vals) // 2
                stats["median"] = (
                    sorted_vals[mid] if len(sorted_vals) % 2 == 1
                    else (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
                )

            # Mode (most frequent)
            freq: dict[Any, int] = {}
            for v in values:
                freq[v] = freq.get(v, 0) + 1
            stats["mode"] = max(freq.items(), key=lambda x: x[1])[0] if freq else None

            self._column_stats[field] = stats

    def _get_fill_value(self, field: str) -> Any:
        """Get the fill value for a field based on strategy."""
        # Constant fill value from config
        if field in self.fill_values:
            return self.fill_values[field]

        # Statistical fill
        if field in self._column_stats:
            stats = self._column_stats[field]
            if self.strategy == MissingValueStrategy.FILL_MEAN and "mean" in stats:
                return stats["mean"]
            if self.strategy == MissingValueStrategy.FILL_MEDIAN and "median" in stats:
                return stats["median"]
            if self.strategy == MissingValueStrategy.FILL_MODE and "mode" in stats:
                return stats["mode"]

        # Forward fill
        if self.strategy == MissingValueStrategy.FILL_FORWARD and field in self._prev_row:
            return self._prev_row[field]

        return None

    def validate(self, row: dict[str, Any], row_index: int = 0) -> MissingValueResult:
        """
        Validate and handle missing values in a row.

        Returns processed row with missing values handled, or error if REJECT strategy.
        """
        self._collect_column_stats(row)

        # Compute stats periodically (every 100 rows)
        if self._stats.total_rows % 100 == 0:
            self._compute_column_stats()

        processed_row = dict(row)
        filled_fields = []
        errors = []

        for field, value in row.items():
            if self._is_missing(value):
                self._stats.record_missing(field)

                # Required fields cannot be missing
                if field in self.required_fields:
                    errors.append({
                        "field": field,
                        "error": "required_field_missing",
                        "message": f"Required field '{field}' is missing",
                    })
                    continue

                # Get fill value based on strategy
                fill_value = self._get_fill_value(field)

                if fill_value is not None:
                    processed_row[field] = fill_value
                    filled_fields.append(field)
                    self._stats.record_filled(field)
                    logger.debug(
                        "Filled missing value",
                        field=field,
                        fill_value=fill_value,
                        strategy=self.strategy.value,
                    )
                else:
                    # No fill value available - reject if REJECT strategy
                    if self.strategy == MissingValueStrategy.REJECT:
                        errors.append({
                            "field": field,
                            "error": "missing_value_no_fill",
                            "message": f"Missing value in '{field}' with no fill strategy available",
                        })
                    # For other strategies without fill value, leave as is

        is_valid = len(errors) == 0

        if not is_valid:
            self._stats.record_rejected()

        # Update previous row for forward fill
        self._prev_row = dict(processed_row) if is_valid else self._prev_row

        return MissingValueResult(
            is_valid=is_valid,
            row_index=row_index,
            processed_row=processed_row if is_valid else None,
            errors=errors,
            filled_fields=filled_fields,
        )

    def _get_fill_value(self, field: str) -> Any:
        """Get fill value based on strategy."""
        # Constant fill
        if self.strategy == MissingValueStrategy.FILL_CONSTANT:
            return self.fill_values.get(field)

        # Statistical fills
        if field in self._column_stats:
            stats = self._column_stats[field]
            if self.strategy == MissingValueStrategy.FILL_MEAN and "mean" in stats:
                return stats["mean"]
            if self.strategy == MissingValueStrategy.FILL_MEDIAN and "median" in stats:
                return stats["median"]
            if self.strategy == MissingValueStrategy.FILL_MODE and "mode" in stats:
                return stats["mode"]

        # Forward fill
        if self.strategy == MissingValueStrategy.FILL_FORWARD and field in self._prev_row:
            return self._prev_row[field]

        return None