"""
Aggregation Engine - Computes aggregations over data streams.

Supports: grouped aggregations, hierarchical aggregations, streaming aggregations.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from shared_sdk.logger import get_logger

logger = get_logger("aggregation")


class AggregationFunction(str, Enum):
    """Supported aggregation functions."""

    COUNT = "count"
    SUM = "sum"
    MEAN = "mean"
    MIN = "min"
    MAX = "max"
    STD = "std"
    VAR = "var"
    FIRST = "first"
    LAST = "last"
    MEDIAN = "median"
    PERCENTILE_25 = "p25"
    PERCENTILE_50 = "p50"
    PERCENTILE_75 = "p75"
    PERCENTILE_90 = "p90"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"
    RATE = "rate"  # events per time unit
    UNIQUE = "unique"  # count unique values
    TOP_K = "top_k"  # most frequent values


@dataclass
class AggregationConfig:
    """Configuration for an aggregation."""

    name: str
    source_field: str  # Field to aggregate
    group_by: list[str] = field(default_factory=list)  # Grouping fields
    functions: list[AggregationFunction] = field(default_factory=lambda: [AggregationFunction.COUNT, AggregationFunction.MEAN])
    time_field: str | None = None  # Optional time field for time-based aggregations
    window: timedelta | None = None  # Time window (None = global)
    emit_on_change: bool = False  # Emit result when group changes


@dataclass
class AggregationResult:
    """Result of aggregation for a row."""

    is_valid: bool
    row_index: int
    original_row: dict[str, Any]
    enhanced_row: dict[str, Any] | None = None
    aggregation_results: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    aggregated_at: datetime = field(default_factory=datetime.utcnow)


class AggregationEngine:
    """
    Computes aggregations over streaming data.

    Maintains stateful aggregations per group.
    Supports incremental updates for streaming scenarios.
    """

    def __init__(self, configs: list[AggregationConfig] | None = None) -> None:
        """
        Initialize aggregation engine.

        Args:
            configs: List of AggregationConfig objects
        """
        self.configs = configs or []

        # State: config_name -> group_key -> aggregation state
        self._state: dict[str, dict[str, dict[str, Any]]] = defaultdict(lambda: defaultdict(dict))

        # For rate calculations
        self._timestamps: dict[str, dict[str, list[datetime]]] = defaultdict(lambda: defaultdict(list))

        self._stats = {
            "total_rows": 0,
            "aggregated_rows": 0,
            "failed_rows": 0,
            "groups_active": 0,
        }

    def add_config(self, config: AggregationConfig) -> None:
        """Add an aggregation configuration."""
        self.configs.append(config)
        logger.debug("Aggregation config added", name=config.name, functions=[f.value for f in config.functions])

    def aggregate(self, row: dict[str, Any], row_index: int = 0) -> AggregationResult:
        """
        Update aggregations with a row and return current results.

        Returns AggregationResult with current aggregation values.
        """
        self._stats["total_rows"] += 1
        enhanced_row = dict(row)
        aggregation_results = {}
        errors = []

        for config in self.configs:
            try:
                result = self._process_aggregation(config, row)
                aggregation_results.update(result)
                enhanced_row.update(result)
            except Exception as e:
                errors.append({"aggregation": config.name, "error": str(e)})
                logger.warning("Aggregation failed", aggregation=config.name, error=str(e))

        is_valid = len(errors) == 0
        if is_valid:
            self._stats["aggregated_rows"] += 1
        else:
            self._stats["failed_rows"] += 1

        return AggregationResult(
            is_valid=is_valid,
            row_index=row_index,
            original_row=row,
            enhanced_row=enhanced_row if is_valid else None,
            aggregation_results=aggregation_results,
            errors=errors,
        )

    def _process_aggregation(self, config: AggregationConfig, row: dict[str, Any]) -> dict[str, Any]:
        """Process a single aggregation configuration."""
        # Get group key
        group_key = self._get_group_key(row, config.group_by)

        # Get value to aggregate
        value = row.get(config.source_field)
        if value is None:
            return {}

        # Get or create group state
        state = self._state[config.name][group_key]
        self._init_state(state, config.functions)

        # Update state
        self._update_state(state, value, config.functions)

        # Handle time-based aggregations
        if config.time_field:
            timestamp = self._get_timestamp(row, config.time_field)
            if timestamp:
                self._timestamps[config.name][group_key].append(timestamp)
                # Clean old timestamps if window specified
                if config.window:
                    cutoff = timestamp - config.window
                    self._timestamps[config.name][group_key] = [
                        t for t in self._timestamps[config.name][group_key] if t >= cutoff
                    ]

        # Compute current aggregation results
        return self._compute_results(config, group_key, state)

    def _get_group_key(self, row: dict[str, Any], group_by: list[str]) -> str:
        """Generate group key from grouping fields."""
        if not group_by:
            return "_global_"
        parts = []
        for field in group_by:
            val = row.get(field, "NULL")
            parts.append(f"{field}={val}")
        return "|".join(parts)

    def _get_timestamp(self, row: dict[str, Any], time_field: str) -> datetime | None:
        """Extract timestamp from row."""
        value = row.get(time_field)
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return None

    def _init_state(self, state: dict[str, Any], functions: list[AggregationFunction]) -> None:
        """Initialize aggregation state."""
        if "count" not in state:
            state["count"] = 0
            state["sum"] = 0.0
            state["sum_sq"] = 0.0
            state["min"] = float('inf')
            state["max"] = float('-inf')
            state["values"] = []  # For median, percentiles
            state["first"] = None
            state["last"] = None
            state["unique_values"] = set()
            state["value_counts"] = defaultdict(int)

    def _update_state(self, state: dict[str, Any], value: Any, functions: list[AggregationFunction]) -> None:
        """Update aggregation state with new value."""
        state["count"] += 1

        if isinstance(value, (int, float)):
            state["sum"] += float(value)
            state["sum_sq"] += float(value) ** 2
            state["min"] = min(state["min"], float(value))
            state["max"] = max(state["max"], float(value))

            # Store for median/percentiles (limit size)
            state["values"].append(float(value))
            if len(state["values"]) > 10000:
                state["values"] = state["values"][-5000:]

        if state["first"] is None:
            state["first"] = value
        state["last"] = value

        if AggregationFunction.UNIQUE in functions or AggregationFunction.TOP_K in functions:
            state["unique_values"].add(value)
            state["value_counts"][value] += 1

    def _compute_results(self, config: AggregationConfig, group_key: str, state: dict[str, Any]) -> dict[str, Any]:
        """Compute aggregation results from state."""
        results = {}
        count = state["count"]

        if count == 0:
            return results

        for func in config.functions:
            feature_name = f"{config.name}_{func.value}"

            if func == AggregationFunction.COUNT:
                results[feature_name] = count

            elif func == AggregationFunction.SUM:
                results[feature_name] = state["sum"]

            elif func == AggregationFunction.MEAN:
                results[feature_name] = state["sum"] / count if count > 0 else 0.0

            elif func == AggregationFunction.MIN:
                results[feature_name] = state["min"] if state["min"] != float('inf') else None

            elif func == AggregationFunction.MAX:
                results[feature_name] = state["max"] if state["max"] != float('-inf') else None

            elif func == AggregationFunction.STD:
                if count > 1:
                    mean = state["sum"] / count
                    variance = (state["sum_sq"] / count) - (mean * mean)
                    results[feature_name] = max(variance, 0) ** 0.5
                else:
                    results[feature_name] = 0.0

            elif func == AggregationFunction.VAR:
                if count > 1:
                    mean = state["sum"] / count
                    variance = (state["sum_sq"] / count) - (mean * mean)
                    results[feature_name] = max(variance, 0)
                else:
                    results[feature_name] = 0.0

            elif func == AggregationFunction.FIRST:
                results[feature_name] = state["first"]

            elif func == AggregationFunction.LAST:
                results[feature_name] = state["last"]

            elif func == AggregationFunction.MEDIAN:
                values = sorted(state["values"])
                n = len(values)
                if n > 0:
                    results[feature_name] = values[n // 2] if n % 2 == 1 else (values[n // 2 - 1] + values[n // 2]) / 2
                else:
                    results[feature_name] = None

            elif func == AggregationFunction.PERCENTILE_25:
                values = sorted(state["values"])
                if values:
                    idx = int(len(values) * 0.25)
                    results[feature_name] = values[idx]
                else:
                    results[feature_name] = None

            elif func == AggregationFunction.PERCENTILE_50:
                values = sorted(state["values"])
                if values:
                    idx = int(len(values) * 0.50)
                    results[feature_name] = values[idx]
                else:
                    results[feature_name] = None

            elif func == AggregationFunction.PERCENTILE_75:
                values = sorted(state["values"])
                if values:
                    idx = int(len(values) * 0.75)
                    results[feature_name] = values[idx]
                else:
                    results[feature_name] = None

            elif func == AggregationFunction.PERCENTILE_90:
                values = sorted(state["values"])
                if values:
                    idx = int(len(values) * 0.90)
                    results[feature_name] = values[idx]
                else:
                    results[feature_name] = None

            elif func == AggregationFunction.PERCENTILE_95:
                values = sorted(state["values"])
                if values:
                    idx = int(len(values) * 0.95)
                    results[feature_name] = values[idx]
                else:
                    results[feature_name] = None

            elif func == AggregationFunction.PERCENTILE_99:
                values = sorted(state["values"])
                if values:
                    idx = int(len(values) * 0.99)
                    results[feature_name] = values[idx]
                else:
                    results[feature_name] = None

            elif func == AggregationFunction.RATE:
                # Events per minute
                timestamps = self._timestamps[config.name].get(group_key, [])
                if len(timestamps) >= 2:
                    time_span = (timestamps[-1] - timestamps[0]).total_seconds() / 60
                    if time_span > 0:
                        results[feature_name] = count / time_span
                    else:
                        results[feature_name] = count
                else:
                    results[feature_name] = 0

            elif func == AggregationFunction.UNIQUE:
                results[feature_name] = len(state["unique_values"])

            elif func == AggregationFunction.TOP_K:
                # Top 5 most frequent values
                sorted_counts = sorted(state["value_counts"].items(), key=lambda x: x[1], reverse=True)
                results[feature_name] = dict(sorted_counts[:5])

        return results

    def aggregate_batch(self, rows: list[dict[str, Any]]) -> list[AggregationResult]:
        """Aggregate a batch of rows."""
        return [self.aggregate(row, i) for i, row in enumerate(rows)]

    def get_valid_rows(self, results: list[AggregationResult]) -> list[dict[str, Any]]:
        """Extract valid enhanced rows."""
        return [r.enhanced_row for r in results if r.is_valid and r.enhanced_row]

    def get_stats(self) -> dict[str, Any]:
        """Get aggregation engine statistics."""
        stats = dict(self._stats)
        total_groups = sum(len(g) for g in self._state.values())
        stats["groups_active"] = total_groups
        if stats["total_rows"] > 0:
            stats["success_rate"] = stats["aggregated_rows"] / stats["total_rows"]
        return stats

    def reset(self) -> None:
        """Reset all aggregation state."""
        self._state.clear()
        self._timestamps.clear()
        self._stats = {
            "total_rows": 0,
            "aggregated_rows": 0,
            "failed_rows": 0,
            "groups_active": 0,
        }
        logger.info("Aggregation engine reset")

    def update_config(self, config: dict[str, Any]) -> None:
        """Update aggregation configuration."""
        if "configs" in config:
            self.configs = [AggregationConfig(**c) for c in config["configs"]]
            self.reset()
        logger.info("Aggregation engine config updated", config_count=len(self.configs))