"""
Data Cleaner - Removes invalid data, outliers, and applies basic cleaning rules.

Supports configurable cleaning rules per field.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from shared_sdk.logger import get_logger

logger = get_logger("data_cleaner")


class CleanAction(str, Enum):
    """Action to take when cleaning rule is violated."""

    REJECT = "reject"           # Mark row as invalid
    REMOVE_FIELD = "remove_field"  # Remove the field from row
    CAP = "cap"                 # Cap value at boundary
    CLIP = "clip"               # Clip to boundary (alias for cap)
    LOG_WARN = "log_warn"       # Log warning but keep value


@dataclass
class CleanRule:
    """A single cleaning rule for a field."""

    field: str
    action: CleanAction = CleanAction.REJECT
    min_value: Any | None = None
    max_value: Any | None = None
    allowed_values: list[Any] | None = None
    forbidden_values: list[Any] | None = None
    pattern: str | None = None  # Regex pattern for string fields
    custom_fn: str | None = None  # Name of custom function (for future extensibility)


@dataclass
class CleanResult:
    """Result of cleaning a single row."""

    is_valid: bool
    row_index: int
    original_row: dict[str, Any]
    cleaned_row: dict[str, Any] | None = None
    removed_fields: list[str] = field(default_factory=list)
    capped_fields: dict[str, Any] = field(default_factory=dict)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    cleaned_at: datetime = field(default_factory=datetime.utcnow)


class DataCleaner:
    """
    Cleans data rows based on configured rules.

    Rules can enforce:
    - Value ranges (min/max)
    - Allowed/forbidden values
    - String patterns
    - Custom validation functions
    """

    def __init__(
        self,
        rules: list[CleanRule] | None = None,
        global_action: CleanAction = CleanAction.REJECT,
    ) -> None:
        """
        Initialize cleaner.

        Args:
            rules: List of field-specific cleaning rules
            global_action: Default action for fields without specific rules
        """
        self.rules = {rule.field: rule for rule in (rules or [])}
        self.global_action = global_action

        # Statistics
        self._stats = {
            "total_rows": 0,
            "valid_rows": 0,
            "rejected_rows": 0,
            "removed_fields": 0,
            "capped_fields": 0,
            "warnings": 0,
        }

    def add_rule(self, rule: CleanRule) -> None:
        """Add or update a cleaning rule."""
        self.rules[rule.field] = rule
        logger.debug("Clean rule added/updated", field=rule.field, action=rule.action.value)

    def remove_rule(self, field: str) -> bool:
        """Remove a cleaning rule."""
        if field in self.rules:
            del self.rules[field]
            return True
        return False

    def clean(self, row: dict[str, Any], row_index: int = 0) -> CleanResult:
        """
        Clean a single row according to rules.

        Returns CleanResult with cleaned row or errors.
        """
        self._stats["total_rows"] += 1
        cleaned_row = dict(row)
        removed_fields = []
        capped_fields = {}
        warnings = []
        errors = []

        for field, rule in self.rules.items():
            if field not in cleaned_row:
                continue

            value = cleaned_row[field]
            action = rule.action
            field_errors = []
            field_warnings = []

            # Range check
            if rule.min_value is not None:
                try:
                    if value < rule.min_value:
                        if action == CleanAction.CAP or action == CleanAction.CLIP:
                            cleaned_row[field] = rule.min_value
                            capped_fields[field] = rule.min_value
                            self._stats["capped_fields"] += 1
                            logger.debug("Value capped at min", field=field, value=value, min=rule.min_value)
                        elif action == CleanAction.REMOVE_FIELD:
                            removed_fields.append(field)
                            del cleaned_row[field]
                            self._stats["removed_fields"] += 1
                        elif action == CleanAction.LOG_WARN:
                            field_warnings.append({"field": field, "issue": "below_min", "value": value})
                        else:  # REJECT
                            field_errors.append({
                                "field": field,
                                "error": "below_minimum",
                                "value": value,
                                "min": rule.min_value,
                            })

                except TypeError:
                    # Incomparable types
                    pass

            if rule.max_value is not None:
                try:
                    if value > rule.max_value:
                        if action == CleanAction.CAP or action == CleanAction.CLIP:
                            cleaned_row[field] = rule.max_value
                            capped_fields[field] = rule.max_value
                            self._stats["capped_fields"] += 1
                        elif action == CleanAction.REMOVE_FIELD:
                            removed_fields.append(field)
                            del cleaned_row[field]
                            self._stats["removed_fields"] += 1
                        elif action == CleanAction.LOG_WARN:
                            field_warnings.append({"field": field, "issue": "above_max", "value": value})
                        else:
                            field_errors.append({
                                "field": field,
                                "error": "above_maximum",
                                "value": value,
                                "max": rule.max_value,
                            })
                except TypeError:
                    pass

            # Allowed values check
            if rule.allowed_values is not None:
                if value not in rule.allowed_values:
                    if action == CleanAction.REMOVE_FIELD:
                        removed_fields.append(field)
                        del cleaned_row[field]
                        self._stats["removed_fields"] += 1
                    elif action == CleanAction.LOG_WARN:
                        field_warnings.append({"field": field, "issue": "not_allowed", "value": value})
                    else:
                        field_errors.append({
                            "field": field,
                            "error": "value_not_allowed",
                            "value": value,
                            "allowed": rule.allowed_values,
                        })

            # Forbidden values check
            if rule.forbidden_values is not None:
                if value in rule.forbidden_values:
                    if action == CleanAction.REMOVE_FIELD:
                        removed_fields.append(field)
                        del cleaned_row[field]
                        self._stats["removed_fields"] += 1
                    elif action == CleanAction.LOG_WARN:
                        field_warnings.append({"field": field, "issue": "forbidden", "value": value})
                    else:
                        field_errors.append({
                            "field": field,
                            "error": "value_forbidden",
                            "value": value,
                        })

            # Pattern check (for strings)
            if rule.pattern and isinstance(value, str):
                import re
                if not re.match(rule.pattern, value):
                    if action == CleanAction.REMOVE_FIELD:
                        removed_fields.append(field)
                        del cleaned_row[field]
                        self._stats["removed_fields"] += 1
                    elif action == CleanAction.LOG_WARN:
                        field_warnings.append({"field": field, "issue": "pattern_mismatch", "value": value})
                    else:
                        field_errors.append({
                            "field": field,
                            "error": "pattern_mismatch",
                            "value": value,
                            "pattern": rule.pattern,
                        })

            if field_errors:
                errors.extend(field_errors)
            if field_warnings:
                warnings.extend(field_warnings)
                self._stats["warnings"] += len(field_warnings)

        # Check fields without specific rules (global action)
        for field, value in row.items():
            if field not in self.rules and value is not None:
                # Could add global validation here if needed
                pass

        is_valid = len(errors) == 0

        if is_valid:
            self._stats["valid_rows"] += 1
        else:
            self._stats["rejected_rows"] += 1
            logger.warning(
                "Data cleaning failed",
                row_index=row_index,
                errors=errors,
            )

        return CleanResult(
            is_valid=is_valid,
            row_index=row_index,
            original_row=row,
            cleaned_row=cleaned_row if is_valid else None,
            removed_fields=removed_fields,
            capped_fields=capped_fields,
            warnings=warnings,
            errors=errors,
        )

    def clean_batch(self, rows: list[dict[str, Any]]) -> list[CleanResult]:
        """Clean a batch of rows."""
        return [self.clean(row, i) for i, row in enumerate(rows)]

    def get_valid_rows(self, results: list[CleanResult]) -> list[dict[str, Any]]:
        """Extract valid cleaned rows."""
        return [r.cleaned_row for r in results if r.is_valid and r.cleaned_row]

    def get_stats(self) -> dict[str, Any]:
        """Get cleaning statistics."""
        stats = dict(self._stats)
        if stats["total_rows"] > 0:
            stats["success_rate"] = stats["valid_rows"] / stats["total_rows"]
        return stats

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            "total_rows": 0,
            "valid_rows": 0,
            "rejected_rows": 0,
            "removed_fields": 0,
            "capped_fields": 0,
            "warnings": 0,
        }

    def update_config(self, rules_config: list[dict[str, Any]]) -> None:
        """Update rules from configuration dict."""
        new_rules = []
        for rule_cfg in rules_config:
            rule = CleanRule(
                field=rule_cfg["field"],
                action=CleanAction(rule_cfg.get("action", "reject")),
                min_value=rule_cfg.get("min_value"),
                max_value=rule_cfg.get("max_value"),
                allowed_values=rule_cfg.get("allowed_values"),
                forbidden_values=rule_cfg.get("forbidden_values"),
                pattern=rule_cfg.get("pattern"),
            )
            new_rules.append(rule)
        self.rules = {rule.field: rule for rule in new_rules}
        logger.info("Data cleaner config updated", rule_count=len(self.rules))