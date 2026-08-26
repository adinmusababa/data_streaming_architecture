"""
Validation Pipeline - Composable pipeline for running multiple validators in sequence.

Combines SchemaValidator, MissingValueValidator, and DuplicateDetector
into a single configurable validation stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from shared_sdk.logger import get_logger

from app.validators.schema_validator import SchemaValidator, SchemaValidationResult
from app.validators.missing_value_validator import (
    MissingValueValidator,
    MissingValueResult,
    MissingValueStrategy,
)
from app.validators.duplicate_detector import DuplicateDetector, DuplicateResult, DuplicateStrategy

logger = get_logger("validation_pipeline")


@dataclass
class ValidationResult:
    """Aggregated result from all validators for a single row."""

    is_valid: bool
    row_index: int
    original_row: dict[str, Any]
    final_row: dict[str, Any] | None = None

    # Per-validator results
    schema_result: SchemaValidationResult | None = None
    missing_value_result: MissingValueResult | None = None
    duplicate_result: DuplicateResult | None = None

    # Aggregated info
    all_errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def error_count(self) -> int:
        return len(self.all_errors)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class ValidationPipeline:
    """
    Composable validation pipeline.

    Runs validators in sequence:
    1. Schema Validation (validates structure/types)
    2. Missing Value Validation (handles null/missing values)
    3. Duplicate Detection (detects duplicate rows)

    Each validator can be enabled/disabled and configured independently.
    Pipeline stops on first failure if strict_mode=True.
    """

    def __init__(
        self,
        schema_validator: SchemaValidator | None = None,
        missing_value_validator: MissingValueValidator | None = None,
        duplicate_detector: DuplicateDetector | None = None,
        strict_mode: bool = False,
    ) -> None:
        """
        Initialize pipeline.

        Args:
            schema_validator: SchemaValidator instance (or None to skip)
            missing_value_validator: MissingValueValidator instance (or None to skip)
            duplicate_detector: DuplicateDetector instance (or None to skip)
            strict_mode: If True, stop pipeline on first validation failure
        """
        self.schema_validator = schema_validator
        self.missing_value_validator = missing_value_validator
        self.duplicate_detector = duplicate_detector
        self.strict_mode = strict_mode

        self._stats = {
            "total_rows": 0,
            "valid_rows": 0,
            "rejected_rows": 0,
            "schema_errors": 0,
            "missing_value_errors": 0,
            "duplicate_errors": 0,
        }

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "ValidationPipeline":
        """
        Create pipeline from configuration dict.

        Expected config structure:
        {
            "schema": {
                "enabled": true,
                "fields": [{"name": "temp", "type": "float", "required": true}],
                "strict": false
            },
            "missing_values": {
                "enabled": true,
                "strategy": "fill_mean",
                "field_config": {"temperature": {"strategy": "fill_median"}}
            },
            "duplicates": {
                "enabled": true,
                "key_fields": ["sensor_id", "timestamp"],
                "strategy": "reject"
            },
            "strict_mode": false
        }
        """
        schema_val = None
        missing_val = None
        dup_detector = None

        if config.get("schema", {}).get("enabled", False):
            schema_cfg = config["schema"]
            schema_val = SchemaValidator(
                schema=schema_cfg.get("fields"),
                strict=schema_cfg.get("strict", False),
                required_fields=schema_cfg.get("required_fields"),
                field_types=schema_cfg.get("field_types"),
            )

        if config.get("missing_values", {}).get("enabled", False):
            mv_cfg = config["missing_values"]
            missing_val = MissingValueValidator(
                strategy=MissingValueStrategy(mv_cfg.get("strategy", "fill_constant")),
                fill_values=mv_cfg.get("fill_values"),
                required_fields=mv_cfg.get("required_fields"),
                numeric_fields=mv_cfg.get("numeric_fields"),
            )

        if config.get("duplicates", {}).get("enabled", False):
            dup_cfg = config["duplicates"]
            dup_detector = DuplicateDetector(
                key_fields=dup_cfg.get("key_fields"),
                strategy=DuplicateStrategy(dup_cfg.get("strategy", "reject")),
                max_memory=dup_cfg.get("max_memory", 100000),
            )

        return cls(
            schema_validator=schema_val,
            missing_value_validator=missing_val,
            duplicate_detector=dup_detector,
            strict_mode=config.get("strict_mode", False),
        )

    def validate(self, row: dict[str, Any], row_index: int = 0) -> ValidationResult:
        """
        Run all enabled validators on a single row.

        Returns aggregated ValidationResult.
        """
        self._stats["total_rows"] += 1

        current_row = row
        all_errors = []
        warnings = []

        # 1. Schema Validation
        schema_result = None
        if self.schema_validator:
            schema_result = self.schema_validator.validate(current_row, row_index)
            if not schema_result.is_valid:
                all_errors.extend([
                    {**e, "validator": "schema"} for e in schema_result.errors
                ])
                self._stats["schema_errors"] += 1
                if self.strict_mode:
                    return self._make_result(
                        False, row_index, row, None,
                        schema_result=schema_result,
                        errors=all_errors, warnings=warnings
                    )
            else:
                current_row = schema_result.validated_data
                # Check for warnings from schema validation
                if hasattr(schema_result, 'warnings') and schema_result.warnings:
                    warnings.extend([
                        {**w, "validator": "schema"} for w in schema_result.warnings
                    ])

        # 2. Missing Value Validation
        missing_result = None
        if self.missing_value_validator:
            missing_result = self.missing_value_validator.validate(current_row, row_index)
            if not missing_result.is_valid:
                all_errors.extend([
                    {**e, "validator": "missing_value"} for e in missing_result.errors
                ])
                self._stats["missing_value_errors"] += 1
                if self.strict_mode:
                    return self._make_result(
                        False, row_index, row, None,
                        schema_result=schema_result,
                        missing_value_result=missing_result,
                        errors=all_errors, warnings=warnings
                    )
            else:
                current_row = missing_result.processed_row
                if missing_result.filled_fields:
                    warnings.append({
                        "validator": "missing_value",
                        "message": f"Filled missing values: {missing_result.filled_fields}",
                        "filled": missing_result.filled_fields,
                    })

        # 3. Duplicate Detection
        duplicate_result = None
        if self.duplicate_detector:
            duplicate_result = self.duplicate_detector.validate(current_row, row_index)
            if not duplicate_result.is_valid:
                all_errors.extend([
                    {**e, "validator": "duplicate"} for e in duplicate_result.errors
                ])
                self._stats["duplicate_errors"] += 1
                # Don't stop on duplicate in strict mode - it's a data quality issue
            elif duplicate_result.is_duplicate:
                warnings.append({
                    "validator": "duplicate",
                    "message": f"Duplicate row detected (key: {duplicate_result.duplicate_key})",
                    "first_seen": duplicate_result.first_seen_index,
                })

        is_valid = len(all_errors) == 0
        final_row = current_row if is_valid else None

        if is_valid:
            self._stats["valid_rows"] += 1
        else:
            self._stats["rejected_rows"] += 1

        return self._make_result(
            is_valid, row_index, row, final_row,
            schema_result=schema_result,
            missing_value_result=missing_result,
            duplicate_result=duplicate_result,
            errors=all_errors,
            warnings=warnings,
        )

    def _make_result(
        self,
        is_valid: bool,
        row_index: int,
        original_row: dict[str, Any],
        final_row: dict[str, Any] | None,
        schema_result: SchemaValidationResult | None = None,
        missing_value_result: MissingValueResult | None = None,
        duplicate_result: DuplicateResult | None = None,
        errors: list[dict[str, Any]] | None = None,
        warnings: list[dict[str, Any]] | None = None,
    ) -> ValidationResult:
        """Create ValidationResult from components."""
        return ValidationResult(
            is_valid=is_valid,
            row_index=row_index,
            original_row=original_row,
            final_row=final_row,
            schema_result=schema_result,
            missing_value_result=missing_value_result,
            duplicate_result=duplicate_result,
            all_errors=errors or [],
            warnings=warnings or [],
        )

    def validate_batch(self, rows: list[dict[str, Any]]) -> list[ValidationResult]:
        """Validate a batch of rows."""
        return [self.validate(row, i) for i, row in enumerate(rows)]

    def get_stats(self) -> dict[str, Any]:
        """Get pipeline statistics."""
        base_stats = dict(self._stats)
        base_stats["success_rate"] = (
            self._stats["valid_rows"] / self._stats["total_rows"]
            if self._stats["total_rows"] > 0 else 0.0
        )

        # Add validator-specific stats
        if self.missing_value_validator:
            base_stats["missing_value_stats"] = self.missing_value_validator.get_stats()
        if self.duplicate_detector:
            base_stats["duplicate_stats"] = self.duplicate_detector.get_stats()

        return base_stats

    def reset(self) -> None:
        """Reset all validators and statistics."""
        self._stats = {
            "total_rows": 0,
            "valid_rows": 0,
            "rejected_rows": 0,
            "schema_errors": 0,
            "missing_value_errors": 0,
            "duplicate_errors": 0,
        }
        if self.missing_value_validator:
            self.missing_value_validator.reset_stats()
        if self.duplicate_detector:
            self.duplicate_detector.reset()
        logger.info("Validation pipeline reset")

    def update_config(self, config: dict[str, Any]) -> None:
        """Update validator configurations at runtime."""
        if "schema" in config and self.schema_validator:
            self.schema_validator.update_schema(config["schema"])
        if "missing_values" in config and self.missing_value_validator:
            mv_cfg = config["missing_values"]
            self.missing_value_validator.update_config(
                strategy=MissingValueStrategy(mv_cfg["strategy"]) if "strategy" in mv_cfg else None,
                fill_values=mv_cfg.get("fill_values"),
                required_fields=mv_cfg.get("required_fields"),
                numeric_fields=mv_cfg.get("numeric_fields"),
            )
        if "duplicates" in config and self.duplicate_detector:
            dup_cfg = config["duplicates"]
            self.duplicate_detector.update_config(
                key_fields=dup_cfg.get("key_fields"),
                strategy=DuplicateStrategy(dup_cfg["strategy"]) if "strategy" in dup_cfg else None,
            )
        if "strict_mode" in config:
            self.strict_mode = config["strict_mode"]
        logger.info("Validation pipeline config updated")