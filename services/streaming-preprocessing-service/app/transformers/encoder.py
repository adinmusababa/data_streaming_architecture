"""
Encoder - Categorical encoding for preprocessing pipeline.

Supports: Label Encoding, One-Hot Encoding, Ordinal Encoding, Binary Encoding, Frequency Encoding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from shared_sdk.logger import get_logger

logger = get_logger("encoder")


class EncodingStrategy(str, Enum):
    """Categorical encoding strategies."""

    LABEL = "label"           # Integer encoding: A=0, B=1, C=2
    ONE_HOT = "one_hot"       # One-hot vectors
    ORDINAL = "ordinal"       # Ordered integer encoding
    BINARY = "binary"         # Binary representation
    FREQUENCY = "frequency"   # Frequency encoding
    TARGET = "target"         # Target encoding (mean target per category)


@dataclass
class EncodingResult:
    """Result of encoding a row."""

    is_valid: bool
    row_index: int
    original_row: dict[str, Any]
    encoded_row: dict[str, Any] | None = None
    new_fields: list[str] = field(default_factory=list)  # Fields added by encoding
    removed_fields: list[str] = field(default_factory=list)  # Original categorical fields removed
    errors: list[dict[str, Any]] = field(default_factory=list)
    encoded_at: datetime = field(default_factory=datetime.utcnow)


class Encoder:
    """
    Encodes categorical fields to numerical representations.

    Maintains learned mappings for consistent encoding across batches.
    """

    def __init__(
        self,
        strategy: EncodingStrategy = EncodingStrategy.LABEL,
        categorical_fields: list[str] | None = None,
        ordinal_mapping: dict[str, list[str]] | None = None,
        handle_unknown: str = "ignore",  # "ignore", "error", "use_encoded_value"
        unknown_value: int = -1,
        drop_first: bool = False,  # For one-hot: drop first category
        max_categories: int = 100,  # Max categories per field
    ) -> None:
        """
        Initialize encoder.

        Args:
            strategy: Encoding strategy to use
            categorical_fields: List of field names to encode
            ordinal_mapping: For ordinal strategy, maps field -> ordered category list
            handle_unknown: How to handle unseen categories ("ignore", "error", "use_encoded_value")
            unknown_value: Encoded value for unknown categories
            drop_first: For one-hot, drop first category to avoid multicollinearity
            max_categories: Maximum categories to encode per field (prevents explosion)
        """
        self.strategy = strategy
        self.categorical_fields = categorical_fields or []
        self.ordinal_mapping = ordinal_mapping or {}
        self.handle_unknown = handle_unknown
        self.unknown_value = unknown_value
        self.drop_first = drop_first
        self.max_categories = max_categories

        # Learned encoders per field
        self._label_encoders: dict[str, dict[str, int]] = {}
        self._categories: dict[str, list[str]] = {}
        self._category_counts: dict[str, dict[str, int]] = {}
        self._fitted = False

        # Statistics
        self._stats = {
            "total_rows": 0,
            "encoded_rows": 0,
            "skipped_rows": 0,
            "categories_learned": {},
            "unknown_encountered": 0,
        }

    def _learn_categories(self, row: dict[str, Any]) -> None:
        """Learn categories from a row (online learning)."""
        for field in self.categorical_fields:
            if field not in row:
                continue
            value = str(row[field]) if row[field] is not None else "NULL"
            if field not in self._category_counts:
                self._category_counts[field] = {}
            self._category_counts[field][value] = self._category_counts[field].get(value, 0) + 1

    def _build_encoders(self) -> None:
        """Build encoders from learned categories."""
        for field, counts in self._category_counts.items():
            # Sort by frequency (most frequent first)
            sorted_cats = sorted(counts.items(), key=lambda x: x[1], reverse=True)

            # Limit categories
            if len(sorted_cats) > self.max_categories:
                sorted_cats = sorted_cats[:self.max_categories]
                logger.warning(f"Field {field} has {len(counts)} categories, limiting to {self.max_categories}")

            self._categories[field] = [cat for cat, _ in sorted_cats]

            if self.strategy == EncodingStrategy.LABEL:
                self._label_encoders[field] = {cat: i for i, cat in enumerate(self._categories[field])}

            elif self.strategy == EncodingStrategy.ORDINAL:
                # Use provided ordinal mapping if available
                if field in self.ordinal_mapping:
                    self._label_encoders[field] = {cat: i for i, cat in enumerate(self.ordinal_mapping[field])}
                else:
                    self._label_encoders[field] = {cat: i for i, cat in enumerate(self._categories[field])}

            elif self.strategy == EncodingStrategy.BINARY:
                # Binary encoding: convert label to binary representation
                n_bits = len(self._categories[field]).bit_length()
                self._label_encoders[field] = {cat: i for i, cat in enumerate(self._categories[field])}
                self._n_bits[field] = n_bits

        self._fitted = True
        self._stats["categories_learned"] = {f: len(cats) for f, cats in self._categories.items()}
        logger.info("Encoder fitted", categories=self._stats["categories_learned"])

    def _ensure_fitted(self) -> None:
        """Ensure encoder is fitted before encoding."""
        if not self._fitted:
            self._build_encoders()

    def encode(self, row: dict[str, Any], row_index: int = 0) -> EncodingResult:
        """Encode categorical fields in a row."""
        self._stats["total_rows"] += 1

        # Learn categories if not fitted
        if not self._fitted:
            self._learn_categories(row)

        self._ensure_fitted()

        encoded_row = dict(row)
        new_fields = []
        removed_fields = []
        errors = []

        for field in self.categorical_fields:
            if field not in row:
                continue

            value = str(row[field]) if row[field] is not None else "NULL"

            if self.strategy == EncodingStrategy.LABEL:
                encoded = self._label_encode(field, value)
                if encoded is not None:
                    encoded_row[field] = encoded
                else:
                    errors.append({"field": field, "error": "unknown_category", "value": value})

            elif self.strategy == EncodingStrategy.ONE_HOT:
                one_hot = self._one_hot_encode(field, value)
                if one_hot:
                    encoded_row.update(one_hot)
                    new_fields.extend(one_hot.keys())
                else:
                    errors.append({"field": field, "error": "unknown_category", "value": value})
                removed_fields.append(field)

            elif self.strategy == EncodingStrategy.ORDINAL:
                encoded = self._label_encode(field, value)
                if encoded is not None:
                    encoded_row[field] = encoded
                else:
                    errors.append({"field": field, "error": "unknown_category", "value": value})

            elif self.strategy == EncodingStrategy.BINARY:
                binary = self._binary_encode(field, value)
                if binary:
                    encoded_row.update(binary)
                    new_fields.extend(binary.keys())
                else:
                    errors.append({"field": field, "error": "unknown_category", "value": value})
                removed_fields.append(field)

            elif self.strategy == EncodingStrategy.FREQUENCY:
                freq = self._frequency_encode(field, value)
                encoded_row[field] = freq

            elif self.strategy == EncodingStrategy.TARGET:
                # Target encoding requires target values - not implemented for streaming
                # Fallback to frequency
                freq = self._frequency_encode(field, value)
                encoded_row[field] = freq

        is_valid = len(errors) == 0

        if is_valid:
            self._stats["encoded_rows"] += 1
        else:
            self._stats["skipped_rows"] += 1
            logger.warning("Encoding failed", row_index=row_index, errors=errors)

        return EncodingResult(
            is_valid=is_valid,
            row_index=row_index,
            original_row=row,
            encoded_row=encoded_row if is_valid else None,
            new_fields=new_fields,
            removed_fields=removed_fields,
            errors=errors,
        )

    def _label_encode(self, field: str, value: str) -> int | None:
        """Label encode a single value."""
        encoder = self._label_encoders.get(field, {})
        if value in encoder:
            return encoder[value]

        # Handle unknown
        if self.handle_unknown == "error":
            raise ValueError(f"Unknown category: {value}")
        elif self.handle_unknown == "use_encoded_value":
            return self.unknown_value
        return None  # ignore

    def _one_hot_encode(self, field: str, value: str) -> dict[str, int] | None:
        """One-hot encode a single value."""
        encoder = self._label_encoders.get(field, {})
        categories = self._categories.get(field, [])

        if value not in encoder:
            if self.handle_unknown == "error":
                raise ValueError(f"Unknown category: {value}")
            elif self.handle_unknown == "use_encoded_value":
                return {f"{field}_{cat}": 0 for cat in categories}
            return None

        idx = encoder[value]
        result = {}
        start = 1 if self.drop_first else 0
        for i, cat in enumerate(categories[start:], start=start):
            col_name = f"{field}_{cat}"
            result[col_name] = 1 if i == idx else 0
        return result

    def _binary_encode(self, field: str, value: str) -> dict[str, int] | None:
        """Binary encode a single value."""
        encoder = self._label_encoders.get(field, {})
        if value not in encoder:
            if self.handle_unknown == "error":
                raise ValueError(f"Unknown category: {value}")
            elif self.handle_unknown == "use_encoded_value":
                n_bits = self._n_bits.get(field, 0)
                return {f"{field}_bin_{i}": 0 for i in range(n_bits)}
            return None

        idx = encoder[value]
        n_bits = self._n_bits.get(field, 0)
        result = {}
        for i in range(n_bits):
            result[f"{field}_bin_{i}"] = (idx >> i) & 1
        return result

    def _frequency_encode(self, field: str, value: str) -> float:
        """Frequency encode a single value."""
        counts = self._category_counts.get(field, {})
        total = sum(counts.values())
        if total == 0:
            return 0.0
        return counts.get(value, 0) / total

    def encode_batch(self, rows: list[dict[str, Any]]) -> list[EncodingResult]:
        """Encode a batch of rows."""
        return [self.encode(row, i) for i, row in enumerate(rows)]

    def get_valid_rows(self, results: list[EncodingResult]) -> list[dict[str, Any]]:
        """Extract valid encoded rows."""
        return [r.encoded_row for r in results if r.is_valid and r.encoded_row]

    def get_stats(self) -> dict[str, Any]:
        """Get encoder statistics."""
        stats = dict(self._stats)
        stats["strategy"] = self.strategy.value
        stats["categorical_fields"] = self.categorical_fields
        stats["fitted"] = self._fitted
        if stats["total_rows"] > 0:
            stats["success_rate"] = stats["encoded_rows"] / stats["total_rows"]
        return stats

    def reset(self) -> None:
        """Reset encoder state."""
        self._label_encoders.clear()
        self._categories.clear()
        self._category_counts.clear()
        self._n_bits = {}
        self._fitted = False
        self._stats = {
            "total_rows": 0,
            "encoded_rows": 0,
            "skipped_rows": 0,
            "categories_learned": {},
            "unknown_encountered": 0,
        }
        logger.info("Encoder reset")

    def update_config(self, config: dict[str, Any]) -> None:
        """Update encoder configuration."""
        if "strategy" in config:
            self.strategy = EncodingStrategy(config["strategy"])
        if "categorical_fields" in config:
            self.categorical_fields = config["categorical_fields"]
        if "ordinal_mapping" in config:
            self.ordinal_mapping = config["ordinal_mapping"]
        if "handle_unknown" in config:
            self.handle_unknown = config["handle_unknown"]
        if "unknown_value" in config:
            self.unknown_value = config["unknown_value"]
        if "drop_first" in config:
            self.drop_first = config["drop_first"]
        if "max_categories" in config:
            self.max_categories = config["max_categories"]

        # Reset encoder state when config changes
        self.reset()
        logger.info("Encoder config updated", strategy=self.strategy.value, fields=self.categorical_fields)