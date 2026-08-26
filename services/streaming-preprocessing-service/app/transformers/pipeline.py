"""
Transformation Pipeline - Composable pipeline for running transformers in sequence.

Combines TypeConverter, DataCleaner, Encoder, Normalizer into a unified transformation stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from shared_sdk.logger import get_logger

from app.transformers.data_cleaner import DataCleaner, CleanResult, CleanRule, CleanAction
from app.transformers.encoder import Encoder, EncodingResult, EncodingStrategy
from app.transformers.normalizer import Normalizer, NormalizationResult, NormalizationStrategy
from app.transformers.type_converter import TypeConverter, TypeConversionResult, TargetType

logger = get_logger("transformation_pipeline")


@dataclass
class TransformationResult:
    """Aggregated result from all transformation stages."""

    is_valid: bool
    row_index: int
    original_row: dict[str, Any]
    final_row: dict[str, Any] | None = None

    # Stage results
    convert_result: TypeConversionResult | None = None
    clean_result: CleanResult | None = None
    encode_result: EncodingResult | None = None
    normalize_result: NormalizationResult | None = None

    # Aggregated info
    all_errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    transformed_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def error_count(self) -> int:
        return len(self.all_errors)


class TransformationPipeline:
    """
    Composable transformation pipeline.

    Runs transformers in sequence:
    1. Type Conversion (string -> target types)
    2. Data Cleaning (remove/cap invalid values)
    3. Encoding (categorical -> numerical)
    4. Normalization (scale numerical features)

    Each stage can be enabled/disabled independently.
    Pipeline stops on first failure if strict_mode=True.
    """

    def __init__(
        self,
        type_converter: TypeConverter | None = None,
        data_cleaner: DataCleaner | None = None,
        encoder: Encoder | None = None,
        normalizer: Normalizer | None = None,
        strict_mode: bool = False,
    ) -> None:
        """
        Initialize pipeline.

        Args:
            type_converter: TypeConverter instance (or None to skip)
            data_cleaner: DataCleaner instance (or None to skip)
            encoder: Encoder instance (or None to skip)
            normalizer: Normalizer instance (or None to skip)
            strict_mode: If True, stop on first transformation failure
        """
        self.type_converter = type_converter
        self.data_cleaner = data_cleaner
        self.encoder = encoder
        self.normalizer = normalizer
        self.strict_mode = strict_mode

        self._stats = {
            "total_rows": 0,
            "valid_rows": 0,
            "rejected_rows": 0,
            "stage_stats": {},
        }

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "TransformationPipeline":
        """
        Create pipeline from configuration dict.

        Expected config structure:
        {
            "type_conversion": {"enabled": true, "field_types": {...}, "auto_infer": true},
            "cleaning": {"enabled": true, "rules": [...]},
            "encoding": {"enabled": true, "strategy": "label", "categorical_fields": [...]},
            "normalization": {"enabled": true, "strategy": "min_max", "fields": [...]},
            "strict_mode": false
        }
        """
        type_converter = None
        if config.get("type_conversion", {}).get("enabled", False):
            tc_cfg = config["type_conversion"]
            type_converter = TypeConverter(
                type_mapping={k: TargetType(v) for k, v in tc_cfg.get("field_types", {}).items()},
                auto_infer=tc_cfg.get("auto_infer", True),
                datetime_formats=tc_cfg.get("datetime_formats"),
                boolean_true_values=tc_cfg.get("boolean_true_values"),
                boolean_false_values=tc_cfg.get("boolean_false_values"),
                fail_on_error=tc_cfg.get("fail_on_error", False),
            )

        data_cleaner = None
        if config.get("cleaning", {}).get("enabled", False):
            cl_cfg = config["cleaning"]
            rules = []
            for rule_cfg in cl_cfg.get("rules", []):
                rules.append(CleanRule(
                    field=rule_cfg["field"],
                    action=CleanAction(rule_cfg.get("action", "reject")),
                    min_value=rule_cfg.get("min_value"),
                    max_value=rule_cfg.get("max_value"),
                    allowed_values=rule_cfg.get("allowed_values"),
                    forbidden_values=rule_cfg.get("forbidden_values"),
                    pattern=rule_cfg.get("pattern"),
                ))
            data_cleaner = DataCleaner(rules=rules)

        encoder = None
        if config.get("encoding", {}).get("enabled", False):
            enc_cfg = config["encoding"]
            encoder = Encoder(
                strategy=EncodingStrategy(enc_cfg.get("strategy", "label")),
                categorical_fields=enc_cfg.get("categorical_fields", []),
                ordinal_mapping=enc_cfg.get("ordinal_mapping"),
                handle_unknown=enc_cfg.get("handle_unknown", "ignore"),
                unknown_value=enc_cfg.get("unknown_value", -1),
                drop_first=enc_cfg.get("drop_first", False),
                max_categories=enc_cfg.get("max_categories", 100),
            )

        normalizer = None
        if config.get("normalization", {}).get("enabled", False):
            norm_cfg = config["normalization"]
            normalizer = Normalizer(
                strategy=NormalizationStrategy(norm_cfg.get("strategy", "min_max")),
                fields=norm_cfg.get("fields", []),
                feature_range=tuple(norm_cfg.get("feature_range", [0.0, 1.0])),
                with_mean=norm_cfg.get("with_mean", True),
                with_std=norm_cfg.get("with_std", True),
                clip=norm_cfg.get("clip", False),
            )

        return cls(
            type_converter=type_converter,
            data_cleaner=data_cleaner,
            encoder=encoder,
            normalizer=normalizer,
            strict_mode=config.get("strict_mode", False),
        )

    def fit(self, rows: list[dict[str, Any]]) -> None:
        """Fit encoder and normalizer on training data."""
        if self.encoder:
            self.encoder.fit(rows)
        if self.normalizer:
            self.normalizer.fit(rows)
        logger.info("Transformation pipeline fitted")

    def transform(self, row: dict[str, Any], row_index: int = 0) -> TransformationResult:
        """
        Run all enabled transformers on a single row.

        Returns aggregated TransformationResult.
        """
        self._stats["total_rows"] += 1
        current_row = dict(row)
        all_errors = []
        warnings = []

        # Stage 1: Type Conversion
        convert_result = None
        if self.type_converter:
            convert_result = self.type_converter.convert(current_row, row_index)
            if not convert_result.is_valid:
                all_errors.extend([{**e, "stage": "type_conversion"} for e in convert_result.errors])
                if self.strict_mode:
                    return self._make_result(False, row_index, row, None, convert_result=convert_result, errors=all_errors)
            else:
                current_row = convert_result.converted_row
                if convert_result.converted_fields:
                    warnings.append({
                        "stage": "type_conversion",
                        "message": f"Converted fields: {convert_result.converted_fields}",
                        "fields": convert_result.converted_fields,
                    })

        # Stage 2: Data Cleaning
        clean_result = None
        if self.data_cleaner:
            clean_result = self.data_cleaner.clean(current_row, row_index)
            if not clean_result.is_valid:
                all_errors.extend([{**e, "stage": "data_cleaning"} for e in clean_result.errors])
                if self.strict_mode:
                    return self._make_result(False, row_index, row, None,
                        convert_result=convert_result, clean_result=clean_result, errors=all_errors, warnings=warnings)
            else:
                current_row = clean_result.cleaned_row
                if clean_result.removed_fields:
                    warnings.append({
                        "stage": "data_cleaning",
                        "message": f"Removed fields: {clean_result.removed_fields}",
                        "removed_fields": clean_result.removed_fields,
                    })
                if clean_result.capped_fields:
                    warnings.append({
                        "stage": "data_cleaning",
                        "message": f"Capped fields: {list(clean_result.capped_fields.keys())}",
                        "capped_fields": clean_result.capped_fields,
                    })

        # Stage 3: Encoding
        encode_result = None
        if self.encoder:
            encode_result = self.encoder.encode(current_row, row_index)
            if not encode_result.is_valid:
                all_errors.extend([{**e, "stage": "encoding"} for e in encode_result.errors])
                if self.strict_mode:
                    return self._make_result(False, row_index, row, None,
                        convert_result=convert_result, clean_result=clean_result,
                        encode_result=encode_result, errors=all_errors, warnings=warnings)
            else:
                current_row = encode_result.encoded_row
                if encode_result.new_fields:
                    warnings.append({
                        "stage": "encoding",
                        "message": f"Added encoded fields: {encode_result.new_fields}",
                        "new_fields": encode_result.new_fields,
                    })
                if encode_result.removed_fields:
                    warnings.append({
                        "stage": "encoding",
                        "message": f"Removed original categorical fields: {encode_result.removed_fields}",
                        "removed_fields": encode_result.removed_fields,
                    })

        # Stage 4: Normalization
        normalize_result = None
        if self.normalizer:
            normalize_result = self.normalizer.normalize(current_row, row_index)
            if not normalize_result.is_valid:
                all_errors.extend([{**e, "stage": "normalization"} for e in normalize_result.errors])
                if self.strict_mode:
                    return self._make_result(False, row_index, row, None,
                        convert_result=convert_result, clean_result=clean_result,
                        encode_result=encode_result, normalize_result=normalize_result,
                        errors=all_errors, warnings=warnings)
            else:
                current_row = normalize_result.normalized_row
                if normalize_result.transformed_fields:
                    warnings.append({
                        "stage": "normalization",
                        "message": f"Normalized fields: {normalize_result.transformed_fields}",
                        "transformed_fields": normalize_result.transformed_fields,
                    })

        is_valid = len(all_errors) == 0
        final_row = current_row if is_valid else None

        if is_valid:
            self._stats["valid_rows"] += 1
        else:
            self._stats["rejected_rows"] += 1

        return self._make_result(is_valid, row_index, row, final_row,
            convert_result=convert_result, clean_result=clean_result,
            encode_result=encode_result, normalize_result=normalize_result,
            errors=all_errors, warnings=warnings)

    def _make_result(
        self,
        is_valid: bool,
        row_index: int,
        original_row: dict[str, Any],
        final_row: dict[str, Any] | None,
        convert_result: TypeConversionResult | None = None,
        clean_result: CleanResult | None = None,
        encode_result: EncodingResult | None = None,
        normalize_result: NormalizationResult | None = None,
        errors: list[dict[str, Any]] | None = None,
        warnings: list[dict[str, Any]] | None = None,
    ) -> TransformationResult:
        """Create TransformationResult from components."""
        return TransformationResult(
            is_valid=is_valid,
            row_index=row_index,
            original_row=original_row,
            final_row=final_row,
            convert_result=convert_result,
            clean_result=clean_result,
            encode_result=encode_result,
            normalize_result=normalize_result,
            all_errors=errors or [],
            warnings=warnings or [],
        )

    def transform_batch(self, rows: list[dict[str, Any]]) -> list[TransformationResult]:
        """Transform a batch of rows."""
        return [self.transform(row, i) for i, row in enumerate(rows)]

    def get_valid_rows(self, results: list[TransformationResult]) -> list[dict[str, Any]]:
        """Extract valid transformed rows."""
        return [r.final_row for r in results if r.is_valid and r.final_row]

    def get_stats(self) -> dict[str, Any]:
        """Get pipeline statistics."""
        stats = dict(self._stats)
        if stats["total_rows"] > 0:
            stats["success_rate"] = stats["valid_rows"] / stats["total_rows"]

        # Add stage-specific stats
        if self.type_converter:
            stats["type_conversion"] = self.type_converter.get_stats()
        if self.data_cleaner:
            stats["data_cleaning"] = self.data_cleaner.get_stats()
        if self.encoder:
            stats["encoding"] = self.encoder.get_stats()
        if self.normalizer:
            stats["normalization"] = self.normalizer.get_stats()

        return stats

    def reset(self) -> None:
        """Reset all transformers and statistics."""
        self._stats = {
            "total_rows": 0,
            "valid_rows": 0,
            "rejected_rows": 0,
            "stage_stats": {},
        }
        if self.type_converter:
            self.type_converter.reset_stats()
        if self.data_cleaner:
            self.data_cleaner.reset_stats()
        if self.encoder:
            self.encoder.reset()
        if self.normalizer:
            self.normalizer.reset_stats()
        logger.info("Transformation pipeline reset")

    def update_config(self, config: dict[str, Any]) -> None:
        """Update pipeline configuration at runtime."""
        if "type_conversion" in config and self.type_converter:
            self.type_converter.update_config(config["type_conversion"])
        if "cleaning" in config and self.data_cleaner:
            self.data_cleaner.update_config(config["cleaning"].get("rules", []))
        if "encoding" in config and self.encoder:
            self.encoder.update_config(config["encoding"])
        if "normalization" in config and self.normalizer:
            self.normalizer.update_config(config["normalization"])
        if "strict_mode" in config:
            self.strict_mode = config["strict_mode"]
        logger.info("Transformation pipeline config updated")