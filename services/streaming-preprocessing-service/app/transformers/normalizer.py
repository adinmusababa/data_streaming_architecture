"""
Normalizer - Feature scaling/normalization for preprocessing pipeline.

Supports: Min-Max, Z-Score (Standardization), Robust Scaling, MaxAbs, Unit Vector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import numpy as np
from shared_sdk.logger import get_logger

logger = get_logger("normalizer")


class NormalizationStrategy(str, Enum):
    """Normalization/scaling strategies."""

    MIN_MAX = "min_max"           # Scale to [0, 1] range
    Z_SCORE = "z_score"           # Standardize to mean=0, std=1
    ROBUST = "robust"             # Robust scaling (median/IQR)
    MAX_ABS = "max_abs"           # Scale by max absolute value
    UNIT_VECTOR = "unit_vector"   # Scale to unit norm
    LOG = "log"                   # Log transformation
    NONE = "none"                 # No transformation


@dataclass
class NormalizationResult:
    """Result of normalizing a row."""

    is_valid: bool
    row_index: int
    original_row: dict[str, Any]
    normalized_row: dict[str, Any] | None = None
    transformed_fields: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    normalized_at: datetime = field(default_factory=datetime.utcnow)


class Normalizer:
    """
    Normalizes/standardizes numerical features.

    Learns parameters from training data (fit) then applies consistently.
    Supports online/streaming updates to statistics.
    """

    def __init__(
        self,
        strategy: NormalizationStrategy = NormalizationStrategy.MIN_MAX,
        fields: list[str] | None = None,
        feature_range: tuple[float, float] = (0.0, 1.0),
        with_mean: bool = True,
        with_std: bool = True,
        clip: bool = False,
    ) -> None:
        """
        Initialize normalizer.

        Args:
            strategy: Normalization strategy
            fields: Fields to normalize (None = all numeric)
            feature_range: Output range for min-max scaling
            with_mean: Center data (z-score)
            with_std: Scale data (z-score)
            clip: Clip values to feature_range (min-max)
        """
        self.strategy = strategy
        self.fields = fields or []
        self.feature_range = feature_range
        self.with_mean = with_mean
        self.with_std = with_std
        self.clip = clip

        # Learned parameters
        self._params: dict[str, dict[str, float]] = {}
        self._fitted = False

        # Online statistics for streaming updates
        self._n_samples = 0
        self._sum: dict[str, float] = {}
        self._sum_sq: dict[str, float] = {}
        self._min: dict[str, float] = {}
        self._max: dict[str, float] = {}
        self._median_buffer: dict[str, list[float]] = {}

        # Statistics
        self._stats = {
            "total_rows": 0,
            "normalized_rows": 0,
            "skipped_rows": 0,
        }

    def fit(self, rows: list[dict[str, Any]]) -> None:
        """Learn normalization parameters from data."""
        if not rows:
            return

        # Auto-detect numeric fields if not specified
        if not self.fields:
            self._auto_detect_fields(rows)

        # Initialize accumulators
        for field in self.fields:
            self._sum[field] = 0.0
            self._sum_sq[field] = 0.0
            self._min[field] = float('inf')
            self._max[field] = float('-inf')
            self._median_buffer[field] = []

        # Collect statistics
        for row in rows:
            self._update_stats(row)

        # Compute parameters
        self._compute_params()
        self._fitted = True
        logger.info("Normalizer fitted", fields=self.fields, strategy=self.strategy.value)

    def _auto_detect_fields(self, rows: list[dict[str, Any]]) -> None:
        """Auto-detect numeric fields from data."""
        if not rows:
            return

        sample = rows[0]
        for field, value in sample.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                # Check if it looks like a feature (not an ID, not too many unique values)
                unique_vals = set()
                for row in rows[:1000]:
                    v = row.get(field)
                    if isinstance(v, (int, float)):
                        unique_vals.add(v)
                if len(unique_vals) > 2:  # More than binary
                    self.fields.append(field)

    def _update_stats(self, row: dict[str, Any]) -> None:
        """Update online statistics with a row."""
        self._n_samples += 1
        for field in self.fields:
            value = row.get(field)
            if value is not None and isinstance(value, (int, float)):
                val = float(value)
                self._sum[field] += val
                self._sum_sq[field] += val * val
                self._min[field] = min(self._min[field], val)
                self._max[field] = max(self._max[field], val)

                # Keep buffer for median (robust scaling)
                if self.strategy == NormalizationStrategy.ROBUST:
                    self._median_buffer[field].append(val)
                    # Limit buffer size
                    if len(self._median_buffer[field]) > 10000:
                        self._median_buffer[field] = self._median_buffer[field][-5000:]

    def _compute_params(self) -> None:
        """Compute normalization parameters from collected statistics."""
        if self._n_samples == 0:
            return

        for field in self.fields:
            params = {}
            min_val = self._min[field]
            max_val = self._max[field]

            if self.strategy == NormalizationStrategy.MIN_MAX:
                params["min"] = min_val
                params["max"] = max_val
                params["range"] = max_val - min_val if max_val != min_val else 1.0
                params["feature_min"] = self.feature_range[0]
                params["feature_max"] = self.feature_range[1]

            elif self.strategy == NormalizationStrategy.Z_SCORE:
                mean = self._sum[field] / self._n_samples
                variance = (self._sum_sq[field] / self._n_samples) - (mean * mean)
                std = max(np.sqrt(max(variance, 0)), 1e-8)
                params["mean"] = mean
                params["std"] = std

            elif self.strategy == NormalizationStrategy.ROBUST:
                buffer = self._median_buffer[field]
                if buffer:
                    sorted_buf = sorted(buffer)
                    n = len(sorted_buf)
                    median = sorted_buf[n // 2] if n % 2 == 1 else (sorted_buf[n // 2 - 1] + sorted_buf[n // 2]) / 2
                    q1 = sorted_buf[n // 4]
                    q3 = sorted_buf[3 * n // 4]
                    iqr = q3 - q1
                    params["median"] = median
                    params["iqr"] = max(iqr, 1e-8)
                    params["q1"] = q1
                    params["q3"] = q3
                else:
                    params["median"] = 0.0
                    params["iqr"] = 1.0

            elif self.strategy == NormalizationStrategy.MAX_ABS:
                params["max_abs"] = max(abs(min_val), abs(max_val))
                if params["max_abs"] == 0:
                    params["max_abs"] = 1.0

            elif self.strategy == NormalizationStrategy.UNIT_VECTOR:
                # For unit vector, we need the norm of the whole row
                # This is computed per-row, not per-field
                pass

            elif self.strategy == NormalizationStrategy.LOG:
                params["shift"] = 0.0
                if min_val <= 0:
                    params["shift"] = abs(min_val) + 1.0

            self._params[field] = params

    def _normalize_value(self, field: str, value: float) -> float:
        """Apply normalization to a single value."""
        if field not in self._params:
            return value

        params = self._params[field]
        val = float(value)

        if self.strategy == NormalizationStrategy.MIN_MAX:
            range_val = params["range"]
            if range_val == 0:
                return params["feature_min"]
            normalized = (val - params["min"]) / range_val
            scaled = normalized * (params["feature_max"] - params["feature_min"]) + params["feature_min"]
            if self.clip:
                scaled = max(params["feature_min"], min(params["feature_max"], scaled))
            return scaled

        elif self.strategy == NormalizationStrategy.Z_SCORE:
            if self.with_mean:
                val = val - params["mean"]
            if self.with_std:
                val = val / params["std"]
            return val

        elif self.strategy == NormalizationStrategy.ROBUST:
            val = (val - params["median"]) / params["iqr"]
            return val

        elif self.strategy == NormalizationStrategy.MAX_ABS:
            return val / params["max_abs"]

        elif self.strategy == NormalizationStrategy.LOG:
            shifted = val + params["shift"]
            if shifted > 0:
                return np.log(shifted)
            return 0.0

        elif self.strategy == NormalizationStrategy.UNIT_VECTOR:
            # Handled at row level
            return val

        return val

    def normalize(self, row: dict[str, Any], row_index: int = 0) -> NormalizationResult:
        """Normalize numerical fields in a row."""
        self._stats["total_rows"] += 1
        normalized_row = dict(row)
        transformed_fields = []
        errors = []

        # Collect values for unit vector normalization
        if self.strategy == NormalizationStrategy.UNIT_VECTOR:
            field_values = {}
            for field in self.fields:
                val = row.get(field)
                if val is not None and isinstance(val, (int, float)):
                    field_values[field] = float(val)

            # Compute norm
            norm = np.sqrt(sum(v * v for v in field_values.values()))
            if norm > 0:
                for field, val in field_values.items():
                    normalized_row[field] = val / norm
                    transformed_fields.append(field)
            else:
                errors.append({"error": "zero_norm", "message": "Row has zero norm"})
        else:
            # Field-wise normalization
            for field in self.fields:
                value = row.get(field)
                if value is not None and isinstance(value, (int, float)):
                    try:
                        normalized_row[field] = self._normalize_value(field, value)
                        transformed_fields.append(field)
                    except Exception as e:
                        errors.append({"field": field, "error": str(e), "value": value})

        is_valid = len(errors) == 0
        if is_valid:
            self._stats["normalized_rows"] += 1
        else:
            self._stats["skipped_rows"] += 1
            logger.warning("Normalization failed", row_index=row_index, errors=errors)

        return NormalizationResult(
            is_valid=is_valid,
            row_index=row_index,
            original_row=row,
            normalized_row=normalized_row if is_valid else None,
            transformed_fields=transformed_fields,
            errors=errors,
        )

    def normalize_batch(self, rows: list[dict[str, Any]]) -> list[NormalizationResult]:
        """Normalize a batch of rows."""
        return [self.normalize(row, i) for i, row in enumerate(rows)]

    def get_valid_rows(self, results: list[NormalizationResult]) -> list[dict[str, Any]]:
        """Extract valid normalized rows."""
        return [r.normalized_row for r in results if r.is_valid and r.normalized_row]

    def partial_fit(self, row: dict[str, Any]) -> None:
        """Update statistics online (for streaming)."""
        self._update_stats(row)
        # Recompute params periodically
        if self._n_samples % 1000 == 0:
            self._compute_params()

    def get_stats(self) -> dict[str, Any]:
        """Get normalizer statistics."""
        stats = dict(self._stats)
        stats["fields"] = self.fields
        stats["strategy"] = self.strategy.value
        stats["fitted"] = self._fitted
        stats["n_samples"] = self._n_samples
        if stats["total_rows"] > 0:
            stats["success_rate"] = stats["normalized_rows"] / stats["total_rows"]
        return stats

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            "total_rows": 0,
            "normalized_rows": 0,
            "skipped_rows": 0,
        }

    def update_config(self, config: dict[str, Any]) -> None:
        """Update normalizer configuration."""
        if "strategy" in config:
            self.strategy = NormalizationStrategy(config["strategy"])
        if "fields" in config:
            self.fields = config["fields"]
        if "feature_range" in config:
            self.feature_range = tuple(config["feature_range"])
        if "with_mean" in config:
            self.with_mean = config["with_mean"]
        if "with_std" in config:
            self.with_std = config["with_std"]
        if "clip" in config:
            self.clip = config["clip"]

        # Reset learned parameters
        self._params = {}
        self._fitted = False
        self._n_samples = 0
        self._sum = {}
        self._sum_sq = {}
        self._min = {}
        self._max = {}
        self._median_buffer = {}

        logger.info("Normalizer config updated", strategy=self.strategy.value, fields=self.fields)