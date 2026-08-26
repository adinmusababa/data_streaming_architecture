"""
Duplicate Detector - Detects and handles duplicate rows in data streams.

Supports multiple strategies: reject, keep_first, keep_last, mark.
Can use full row comparison or specific key fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from shared_sdk.logger import get_logger

logger = get_logger("duplicate_detector")


class DuplicateStrategy(str, Enum):
    """Strategy for handling duplicates."""

    REJECT = "reject"          # Reject duplicate rows (keep first)
    KEEP_FIRST = "keep_first"  # Keep first occurrence, reject subsequent
    KEEP_LAST = "keep_last"    # Keep last occurrence (requires buffering)
    MARK = "mark"              # Add metadata flag, don't reject


@dataclass
class DuplicateResult:
    """Result of duplicate detection for a single row."""

    is_valid: bool
    row_index: int
    original_row: dict[str, Any]
    processed_row: dict[str, Any] | None = None
    is_duplicate: bool = False
    duplicate_key: str | None = None
    first_seen_index: int | None = None
    strategy: DuplicateStrategy = DuplicateStrategy.REJECT
    errors: list[dict[str, Any]] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)


class DuplicateDetector:
    """
    Detects duplicate rows in a data stream.

    Tracks seen rows using a hash of key fields (or full row).
    Supports configurable strategy for handling duplicates.
    """

    def __init__(
        self,
        key_fields: list[str] | None = None,
        strategy: DuplicateStrategy = DuplicateStrategy.REJECT,
        max_memory: int = 100000,
    ) -> None:
        """
        Initialize detector.

        Args:
            key_fields: List of field names to use as duplicate key.
                       If None, uses full row hash.
            strategy: How to handle duplicates
            max_memory: Maximum number of keys to track (prevents memory growth)
        """
        self.key_fields = key_fields
        self.strategy = strategy
        self.max_memory = max_memory

        # Track seen keys: key -> first_seen_index
        self._seen_keys: dict[str, int] = {}
        # Track counts for statistics
        self._key_counts: dict[str, int] = {}

    def _make_key(self, row: dict[str, Any]) -> str:
        """Create a hashable key from row."""
        if self.key_fields:
            key_parts = [str(row.get(f, "")) for f in self.key_fields]
        else:
            # Use sorted items for consistent hashing
            key_parts = [f"{k}={v}" for k, v in sorted(row.items())]
        return "|".join(key_parts)

    def _evict_old_keys(self) -> None:
        """Evict oldest keys if memory limit exceeded."""
        if len(self._seen_keys) >= self.max_memory:
            # Remove oldest 10%
            evict_count = max(1, self.max_memory // 10)
            oldest_keys = sorted(self._seen_keys.items(), key=lambda x: x[1])[:evict_count]
            for key, _ in oldest_keys:
                self._seen_keys.pop(key, None)
                self._key_counts.pop(key, None)

    def validate(self, row: dict[str, Any], row_index: int = 0) -> DuplicateResult:
        """
        Check a single row for duplicates.

        Returns:
            DuplicateResult with validation status and processed row.
        """
        key = self._make_key(row)
        is_duplicate = key in self._seen_keys
        first_seen = self._seen_keys.get(key)
        errors = []
        processed_row = dict(row)

        if is_duplicate:
            self._key_counts[key] = self._key_counts.get(key, 1) + 1

            if self.strategy == DuplicateStrategy.REJECT:
                errors.append({
                    "field": "_duplicate",
                    "error": "duplicate_row",
                    "message": f"Duplicate row detected (key: {key})",
                    "first_seen_index": first_seen,
                })
                processed_row = None

            elif self.strategy == DuplicateStrategy.KEEP_FIRST:
                errors.append({
                    "field": "_duplicate",
                    "error": "duplicate_row",
                    "message": f"Duplicate row rejected (keeping first at index {first_seen})",
                    "first_seen_index": first_seen,
                })
                processed_row = None

            elif self.strategy == DuplicateStrategy.MARK:
                processed_row["_is_duplicate"] = True
                processed_row["_duplicate_key"] = key
                processed_row["_first_seen_index"] = first_seen
                logger.debug("Duplicate marked", key=key, current_index=row_index, first_index=first_seen)

        else:
            # First time seeing this key
            self._seen_keys[key] = row_index
            self._key_counts[key] = 1
            self._evict_old_keys()

        is_valid = len(errors) == 0

        if not is_valid:
            logger.warning(
                "Duplicate validation failed",
                row_index=row_index,
                key=key,
                strategy=self.strategy.value,
                errors=errors,
            )

        return DuplicateResult(
            is_valid=is_valid,
            row_index=row_index,
            original_row=row,
            processed_row=processed_row if is_valid else None,
            is_duplicate=is_duplicate,
            duplicate_key=key,
            first_seen_index=first_seen,
            strategy=self.strategy,
            errors=errors,
        )

    def validate_batch(self, rows: list[dict[str, Any]]) -> list[DuplicateResult]:
        """Validate a batch of rows."""
        return [self.validate(row, i) for i, row in enumerate(rows)]

    def reset(self) -> None:
        """Reset detector state (for new stream)."""
        self._seen_keys.clear()
        self._key_counts.clear()
        logger.info("Duplicate detector reset")

    def get_stats(self) -> dict[str, Any]:
        """Get duplicate detection statistics."""
        total_seen = len(self._seen_keys)
        total_duplicates = sum(c - 1 for c in self._key_counts.values() if c > 1)
        return {
            "unique_keys": total_seen,
            "total_duplicates": total_duplicates,
            "duplicate_groups": sum(1 for c in self._key_counts.values() if c > 1),
        }

    def update_config(
        self,
        key_fields: list[str] | None = None,
        strategy: DuplicateStrategy | None = None,
    ) -> None:
        """Update configuration at runtime."""
        if key_fields is not None:
            self.key_fields = key_fields
        if strategy is not None:
            self.strategy = strategy
        # Reset on config change since key definition changed
        self.reset()
        logger.info(
            "Duplicate detector config updated",
            key_fields=self.key_fields,
            strategy=self.strategy.value,
        )