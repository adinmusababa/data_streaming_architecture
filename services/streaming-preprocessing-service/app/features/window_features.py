"""
Window Features - Time-window based feature extraction for streaming data.

Supports tumbling, sliding, and session windows with various aggregations.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from shared_sdk.logger import get_logger

logger = get_logger("window_features")


class WindowType(str, Enum):
    """Types of time windows."""

    TUMBLING = "tumbling"       # Fixed-size, non-overlapping
    SLIDING = "sliding"         # Fixed-size, overlapping
    SESSION = "session"         # Dynamic, activity-based
    GLOBAL = "global"           # Entire stream


class WindowAggregation(str, Enum):
    """Aggregation functions for window features."""

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
    UNIQUE = "unique"
    RATE = "rate"  # Events per minute


@dataclass
class WindowConfig:
    """Configuration for a window feature."""

    name: str
    source_field: str              # Field to aggregate
    time_field: str                # Timestamp field
    window_type: WindowType = WindowType.SLIDING
    window_size: timedelta | None = None  # Window duration
    slide_size: timedelta | None = None   # Slide duration (for sliding)
    aggregations: list[WindowAggregation] = field(default_factory=lambda: [WindowAggregation.COUNT, WindowAggregation.MEAN])
    group_by: list[str] | None = None     # Grouping fields
    watermark_delay: timedelta | None = None  # Allowed lateness
    emit_on_window_close: bool = True       # Only emit when window closes


@dataclass
class WindowResult:
    """Result of window feature extraction for a row."""

    is_valid: bool
    row_index: int
    original_row: dict[str, Any]
    enhanced_row: dict[str, Any] | None = None
    window_features: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=datetime.utcnow)


class WindowFeatureExtractor:
    """
    Extracts time-window based features from streaming data.

    Maintains window state per group and computes aggregations incrementally.
    """

    def __init__(self, configs: list[WindowConfig] | None = None) -> None:
        """
        Initialize window feature extractor.

        Args:
            configs: List of WindowConfig objects
        """
        self.configs = configs or []

        # State: config_name -> group_key -> list of (timestamp, value) in window
        self._windows: dict[str, dict[str, list[tuple[datetime, float]]]] = defaultdict(lambda: defaultdict(list))

        # For session windows: track last activity per group
        self._last_activity: dict[str, dict[str, datetime]] = defaultdict(dict)

        self._stats = {
            "total_rows": 0,
            "extracted_rows": 0,
            "failed_rows": 0,
            "windows_active": 0,
        }

    def add_config(self, config: WindowConfig) -> None:
        """Add a window configuration."""
        self.configs.append(config)
        logger.debug("Window config added", name=config.name, type=config.window_type.value)

    def extract(self, row: dict[str, Any], row_index: int = 0) -> WindowResult:
        """
        Extract window features for a row.

        Updates window state and returns current window aggregations.
        """
        self._stats["total_rows"] += 1
        enhanced_row = dict(row)
        window_features = {}
        errors = []

        # Get timestamp
        timestamp = self._get_timestamp(row)
        if timestamp is None:
            errors.append({"error": "missing_timestamp", "message": "No valid timestamp field found"})
            return self._make_result(False, row_index, row, None, {}, errors)

        for config in self.configs:
            try:
                result = self._process_window(config, row, timestamp)
                window_features.update(result)
                enhanced_row.update(result)
            except Exception as e:
                errors.append({"window": config.name, "error": str(e)})
                logger.warning("Window extraction failed", window=config.name, error=str(e))

        is_valid = len(errors) == 0
        if is_valid:
            self._stats["extracted_rows"] += 1
        else:
            self._stats["failed_rows"] += 1

        self._stats["windows_active"] = sum(len(w) for w in self._windows.values())

        return self._make_result(is_valid, row_index, row, enhanced_row if is_valid else None, window_features, errors)

    def _get_timestamp(self, row: dict[str, Any]) -> datetime | None:
        """Extract timestamp from row."""
        # Try common timestamp fields
        for field in ["timestamp", "time", "datetime", "event_time", "@timestamp"]:
            if field in row:
                value = row[field]
                if isinstance(value, datetime):
                    return value
                if isinstance(value, (int, float)):
                    return datetime.fromtimestamp(value)
                if isinstance(value, str):
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"]:
                        try:
                            return datetime.strptime(value, fmt)
                        except ValueError:
                            continue
        return None

    def _get_group_key(self, row: dict[str, Any], group_by: list[str] | None) -> str:
        """Generate group key from row."""
        if not group_by:
            return "_global_"
        parts = []
        for field in group_by:
            val = row.get(field, "NULL")
            parts.append(f"{field}={val}")
        return "|".join(parts)

    def _process_window(self, config: WindowConfig, row: dict[str, Any], timestamp: datetime) -> dict[str, Any]:
        """Process a single window configuration."""
        # Get value to aggregate
        value = row.get(config.source_field)
        if value is None:
            return {}

        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return {}

        # Get group key
        group_key = self._get_group_key(row, config.group_by)

        # Add to window
        window_key = config.name
        window_data = self._windows[window_key][group_key]
        window_data.append((timestamp, num_value))

        # Evict old data based on window type
        self._evict_old_data(config, window_data, timestamp)

        # Compute aggregations
        return self._compute_aggregations(config, group_key, window_data, timestamp)

    def _evict_old_data(self, config: WindowConfig, window_data: list[tuple[datetime, float]], current_time: datetime) -> None:
        """Remove data points outside the window."""
        if config.window_type == WindowType.TUMBLING:
            # Tumbling: window aligned to fixed boundaries
            if config.window_size:
                window_start = self._get_tumbling_window_start(current_time, config.window_size)
                cutoff = window_start
                window_data[:] = [(t, v) for t, v in window_data if t >= cutoff]

        elif config.window_type == WindowType.SLIDING:
            # Sliding: keep data within window_size of current time
            if config.window_size:
                cutoff = current_time - config.window_size
                window_data[:] = [(t, v) for t, v in window_data if t >= cutoff]

        elif config.window_type == WindowType.SESSION:
            # Session: keep data since last activity + gap
            if config.window_size:
                last_time = self._last_activity.get(config.name, {}).get(group_key)
                if last_time and (current_time - last_time) > config.window_size:
                    # Session gap exceeded - clear window
                    window_data.clear()
                self._last_activity[config.name][group_key] = current_time

        elif config.window_type == WindowType.GLOBAL:
            # Global: keep all data (with optional watermark)
            if config.watermark_delay:
                cutoff = current_time - config.watermark_delay
                window_data[:] = [(t, v) for t, v in window_data if t >= cutoff]

    def _get_tumbling_window_start(self, timestamp: datetime, window_size: timedelta) -> datetime:
        """Calculate tumbling window start time."""
        # Align to epoch
        epoch = datetime(1970, 1, 1)
        seconds = (timestamp - epoch).total_seconds()
        window_seconds = int(seconds // window_size.total_seconds()) * window_size.total_seconds()
        return epoch + timedelta(seconds=window_seconds)

    def _compute_aggregations(
        self,
        config: WindowConfig,
        group_key: str,
        window_data: list[tuple[datetime, float]],
        current_time: datetime
    ) -> dict[str, Any]:
        """Compute aggregations from window data."""
        if not window_data:
            return {}

        values = [v for _, v in window_data]
        count = len(values)

        results = {}

        for agg in config.aggregations:
            feature_name = f"{config.name}_{agg.value}"

            if agg == WindowAggregation.COUNT:
                results[feature_name] = count

            elif agg == WindowAggregation.SUM:
                results[feature_name] = sum(values)

            elif agg == WindowAggregation.MEAN:
                results[feature_name] = sum(values) / count if count > 0 else 0.0

            elif agg == WindowAggregation.MIN:
                results[feature_name] = min(values)

            elif agg == WindowAggregation.MAX:
                results[feature_name] = max(values)

            elif agg == WindowAggregation.STD:
                if count > 1:
                    mean = sum(values) / count
                    variance = sum((v - mean) ** 2 for v in values) / (count - 1)
                    results[feature_name] = variance ** 0.5
                else:
                    results[feature_name] = 0.0

            elif agg == WindowAggregation.VAR:
                if count > 1:
                    mean = sum(values) / count
                    variance = sum((v - mean) ** 2 for v in values) / (count - 1)
                    results[feature_name] = variance
                else:
                    results[feature_name] = 0.0

            elif agg == WindowAggregation.FIRST:
                results[feature_name] = values[0]

            elif agg == WindowAggregation.LAST:
                results[feature_name] = values[-1]

            elif agg == WindowAggregation.MEDIAN:
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                results[feature_name] = (
                    sorted_vals[n // 2] if n % 2 == 1
                    else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
                )

            elif agg in (WindowAggregation.PERCENTILE_25, WindowAggregation.PERCENTILE_50,
                        WindowAggregation.PERCENTILE_75, WindowAggregation.PERCENTILE_90,
                        WindowAggregation.PERCENTILE_95, WindowAggregation.PERCENTILE_99):
                p = {"p25": 0.25, "p50": 0.50, "p75": 0.75, "p90": 0.90, "p95": 0.95, "p99": 0.99}[agg.value]
                sorted_vals = sorted(values)
                idx = int(len(sorted_vals) * p)
                idx = min(idx, len(sorted_vals) - 1)
                results[feature_name] = sorted_vals[idx]

            elif agg == WindowAggregation.UNIQUE:
                results[feature_name] = len(set(values))

            elif agg == WindowAggregation.RATE:
                # Events per minute
                if len(window_data) >= 2:
                    time_span = (window_data[-1][0] - window_data[0][0]).total_seconds() / 60
                    results[feature_name] = count / time_span if time_span > 0 else count
                else:
                    results[feature_name] = 0

        return results

    def extract_batch(self, rows: list[dict[str, Any]]) -> list[WindowResult]:
        """Extract window features for a batch of rows."""
        return [self.extract(row, i) for i, row in enumerate(rows)]

    def get_valid_rows(self, results: list[WindowResult]) -> list[dict[str, Any]]:
        """Extract valid enhanced rows."""
        return [r.enhanced_row for r in results if r.is_valid and r.enhanced_row]

    def get_stats(self) -> dict[str, Any]:
        """Get extractor statistics."""
        stats = dict(self._stats)
        if stats["total_rows"] > 0:
            stats["success_rate"] = stats["extracted_rows"] / stats["total_rows"]
        return stats

    def reset(self) -> None:
        """Reset window state and statistics."""
        self._windows.clear()
        self._last_activity.clear()
        self._stats = {
            "total_rows": 0,
            "extracted_rows": 0,
            "failed_rows": 0,
            "windows_active": 0,
        }
        logger.info("Window feature extractor reset")

    def update_config(self, config: dict[str, Any]) -> None:
        """Update window configurations."""
        if "configs" in config:
            self.configs = [WindowConfig(**c) for c in config["configs"]]
            self.reset()
        logger.info("Window feature extractor config updated", config_count=len(self.configs))

    def _make_result(
        self,
        is_valid: bool,
        row_index: int,
        original_row: dict[str, Any],
        enhanced_row: dict[str, Any] | None,
        window_features: dict[str, Any],
        errors: list[dict[str, Any]],
    ) -> WindowResult:
        """Create WindowResult from components."""
        return WindowResult(
            is_valid=is_valid,
            row_index=row_index,
            original_row=original_row,
            enhanced_row=enhanced_row,
            window_features=window_features,
            errors=errors,
        )