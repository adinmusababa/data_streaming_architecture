"""
Feature Builder - Creates derived features from raw data.

Supports: mathematical operations, datetime features, text features, interaction features.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from shared_sdk.logger import get_logger

logger = get_logger("feature_builder")


class FeatureType(str, Enum):
    """Types of derived features."""

    ARITHMETIC = "arithmetic"          # add, subtract, multiply, divide
    DATETIME = "datetime"              # hour, day, month, weekday, etc.
    TEXT = "text"                      # length, word_count, etc.
    INTERACTION = "interaction"        # product, ratio of two fields
    CONDITIONAL = "conditional"        # if-then-else features
    CUSTOM = "custom"                  # custom function


@dataclass
class FeatureDefinition:
    """Definition of a derived feature."""

    name: str
    feature_type: FeatureType
    expression: str | Callable  # e.g., "field1 + field2" or lambda row: ...
    dependencies: list[str] = field(default_factory=list)  # Fields needed
    output_type: str = "float"
    description: str = ""


@dataclass
class FeatureResult:
    """Result of feature building for a row."""

    is_valid: bool
    row_index: int
    original_row: dict[str, Any]
    enhanced_row: dict[str, Any] | None = None
    new_features: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    built_at: datetime = field(default_factory=datetime.utcnow)


class FeatureBuilder:
    """
    Builds derived features from raw data fields.

    Supports multiple feature types:
    - Arithmetic: field1 + field2, field1 * field2, etc.
    - Datetime: hour, day_of_week, month, is_weekend, etc.
    - Text: length, word_count, character_count, etc.
    - Interaction: field1 * field2, field1 / field2, etc.
    - Conditional: if field > 0 then 1 else 0
    - Custom: user-defined functions
    """

    def __init__(
        self,
        feature_definitions: list[FeatureDefinition] | None = None,
        safe_mode: bool = True,
    ) -> None:
        """
        Initialize feature builder.

        Args:
            feature_definitions: List of FeatureDefinition objects
            safe_mode: If True, catch errors and set feature to None; else raise
        """
        self.feature_definitions = feature_definitions or []
        self.safe_mode = safe_mode

        # Built-in feature functions
        self._datetime_features = {
            "hour": lambda dt: dt.hour,
            "day": lambda dt: dt.day,
            "month": lambda dt: dt.month,
            "year": lambda dt: dt.year,
            "weekday": lambda dt: dt.weekday(),  # 0=Monday
            "is_weekend": lambda dt: 1 if dt.weekday() >= 5 else 0,
            "quarter": lambda dt: (dt.month - 1) // 3 + 1,
            "day_of_year": lambda dt: dt.timetuple().tm_yday,
            "week_of_year": lambda dt: dt.isocalendar()[1],
            "is_month_start": lambda dt: 1 if dt.day == 1 else 0,
            "is_month_end": lambda dt: 1 if dt.day == 28 else 0,  # Simplified
        }

        self._text_features = {
            "length": lambda s: len(str(s)),
            "word_count": lambda s: len(str(s).split()),
            "char_count": lambda s: len(str(s).replace(" ", "")),
            "uppercase_count": lambda s: sum(1 for c in str(s) if c.isupper()),
            "digit_count": lambda s: sum(1 for c in str(s) if c.isdigit()),
            "special_char_count": lambda s: sum(1 for c in str(s) if not c.isalnum() and not c.isspace()),
        }

        self._stats = {
            "total_rows": 0,
            "enhanced_rows": 0,
            "failed_rows": 0,
            "features_built": {},
        }

    def add_feature(self, definition: FeatureDefinition) -> None:
        """Add a feature definition."""
        self.feature_definitions.append(definition)

    def remove_feature(self, name: str) -> bool:
        """Remove a feature definition by name."""
        for i, fd in enumerate(self.feature_definitions):
            if fd.name == name:
                del self.feature_definitions[i]
                return True
        return False

    def build(self, row: dict[str, Any], row_index: int = 0) -> FeatureResult:
        """
        Build all defined features for a row.

        Returns FeatureResult with enhanced row containing new features.
        """
        self._stats["total_rows"] += 1
        enhanced_row = dict(row)
        new_features = {}
        errors = []

        for feat_def in self.feature_definitions:
            # Check if all dependencies are present
            missing_deps = [dep for dep in feat_def.dependencies if dep not in row]
            if missing_deps:
                if self.safe_mode:
                    errors.append({
                        "feature": feat_def.name,
                        "error": "missing_dependencies",
                        "missing": missing_deps,
                    })
                    enhanced_row[feat_def.name] = None
                    continue
                else:
                    raise ValueError(f"Feature '{feat_def.name}' missing dependencies: {missing_deps}")

            try:
                value = self._compute_feature(feat_def, row)
                enhanced_row[feat_def.name] = value
                new_features[feat_def.name] = value
                self._stats["features_built"][feat_def.name] = \
                    self._stats["features_built"].get(feat_def.name, 0) + 1
            except Exception as e:
                error_info = {"feature": feat_def.name, "error": str(e)}
                errors.append(error_info)
                if self.safe_mode:
                    enhanced_row[feat_def.name] = None
                else:
                    raise

        is_valid = len(errors) == 0
        if is_valid:
            self._stats["enhanced_rows"] += 1
        else:
            self._stats["failed_rows"] += 1
            logger.warning("Feature building failed", row_index=row_index, errors=errors)

        return FeatureResult(
            is_valid=is_valid,
            row_index=row_index,
            original_row=row,
            enhanced_row=enhanced_row if is_valid else None,
            new_features=new_features,
            errors=errors,
        )

    def _compute_feature(self, feat_def: FeatureDefinition, row: dict[str, Any]) -> Any:
        """Compute a single feature based on its definition."""
        if feat_def.feature_type == FeatureType.ARITHMETIC:
            return self._eval_arithmetic(feat_def.expression, row)

        elif feat_def.feature_type == FeatureType.DATETIME:
            return self._extract_datetime_feature(feat_def.expression, row)

        elif feat_def.feature_type == FeatureType.TEXT:
            return self._extract_text_feature(feat_def.expression, row)

        elif feat_def.feature_type == FeatureType.INTERACTION:
            return self._compute_interaction(feat_def.expression, row)

        elif feat_def.feature_type == FeatureType.CONDITIONAL:
            return self._eval_conditional(feat_def.expression, row)

        elif feat_def.feature_type == FeatureType.CUSTOM:
            if callable(feat_def.expression):
                return feat_def.expression(row)
            raise ValueError(f"Custom feature must be callable: {feat_def.name}")

        raise ValueError(f"Unknown feature type: {feat_def.feature_type}")

    def _eval_arithmetic(self, expression: str, row: dict[str, Any]) -> float:
        """Evaluate arithmetic expression using row fields."""
        # Simple safe evaluation: replace field names with values
        import re

        # Find all field references (word characters)
        fields = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expression)
        local_vars = {}

        for field in fields:
            if field in row:
                local_vars[field] = row[field]
            elif field not in ['and', 'or', 'not', 'True', 'False', 'None']:
                local_vars[field] = 0  # Default for unknown fields

        # Evaluate safely
        try:
            return eval(expression, {"__builtins__": {}}, local_vars)
        except Exception:
            return 0.0

    def _extract_datetime_feature(self, feature_name: str, row: dict[str, Any]) -> Any:
        """Extract datetime feature from a datetime field."""
        # Find datetime field in row
        datetime_fields = [k for k, v in row.items() if isinstance(v, datetime)]

        if not datetime_fields:
            return None

        dt = row[datetime_fields[0]]  # Use first datetime field
        if feature_name in self._datetime_features:
            return self._datetime_features[feature_name](dt)
        return None

    def _extract_text_feature(self, feature_name: str, row: dict[str, Any]) -> Any:
        """Extract text feature from a string field."""
        # Find string fields
        string_fields = [k for k, v in row.items() if isinstance(v, str)]

        if not string_fields:
            return None

        text = row[string_fields[0]]  # Use first string field
        if feature_name in self._text_features:
            return self._text_features[feature_name](text)
        return None

    def _compute_interaction(self, expression: str, row: dict[str, Any]) -> float:
        """Compute interaction feature (product, ratio, etc.)."""
        return self._eval_arithmetic(expression, row)

    def _eval_conditional(self, expression: str, row: dict[str, Any]) -> float:
        """Evaluate conditional expression (ternary)."""
        # Support: "condition ? true_val : false_val"
        # or: "if condition then true_val else false_val"
        import re

        # Try ternary format
        ternary_match = re.match(r'(.+?)\s*\?\s*(.+?)\s*:\s*(.+)', expression)
        if ternary_match:
            condition, true_val, false_val = ternary_match.groups()
            cond_result = self._eval_arithmetic(condition.strip(), row)
            if cond_result:
                return self._eval_arithmetic(true_val.strip(), row)
            return self._eval_arithmetic(false_val.strip(), row)

        # Try if-then-else format
        if_match = re.match(r'if\s+(.+?)\s+then\s+(.+?)\s+else\s+(.+)', expression, re.IGNORECASE)
        if if_match:
            condition, true_val, false_val = if_match.groups()
            cond_result = self._eval_arithmetic(condition.strip(), row)
            if cond_result:
                return self._eval_arithmetic(true_val.strip(), row)
            return self._eval_arithmetic(false_val.strip(), row)

        return 0.0

    def build_batch(self, rows: list[dict[str, Any]]) -> list[FeatureResult]:
        """Build features for a batch of rows."""
        return [self.build(row, i) for i, row in enumerate(rows)]

    def get_valid_rows(self, results: list[FeatureResult]) -> list[dict[str, Any]]:
        """Extract valid enhanced rows."""
        return [r.enhanced_row for r in results if r.is_valid and r.enhanced_row]

    def get_stats(self) -> dict[str, Any]:
        """Get feature builder statistics."""
        stats = dict(self._stats)
        if stats["total_rows"] > 0:
            stats["success_rate"] = stats["enhanced_rows"] / stats["total_rows"]
        return stats

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = {
            "total_rows": 0,
            "enhanced_rows": 0,
            "failed_rows": 0,
            "features_built": {},
        }

    def update_config(self, config: dict[str, Any]) -> None:
        """Update feature builder configuration."""
        if "feature_definitions" in config:
            self.feature_definitions = [
                FeatureDefinition(**fd) for fd in config["feature_definitions"]
            ]
        if "safe_mode" in config:
            self.safe_mode = config["safe_mode"]
        logger.info("Feature builder config updated", feature_count=len(self.feature_definitions))