"""
Feature Pipeline - Composable pipeline for running feature engineering stages in sequence.

Combines FeatureBuilder, WindowFeatureExtractor, AggregationEngine into a unified feature stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from shared_sdk.logger import get_logger

from app.features.feature_builder import FeatureBuilder, FeatureDefinition, FeatureResult
from app.features.window_features import WindowFeatureExtractor, WindowConfig, WindowResult
from app.features.aggregation import AggregationEngine, AggregationConfig, AggregationResult

logger = get_logger("feature_pipeline")


@dataclass
class FeaturePipelineResult:
    """Aggregated result from all feature engineering stages."""

    is_valid: bool
    row_index: int
    original_row: dict[str, Any]
    final_row: dict[str, Any] | None = None

    # Stage results
    builder_result: FeatureResult | None = None
    window_result: WindowResult | None = None
    aggregation_result: AggregationResult | None = None

    # Aggregated info
    all_errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    processed_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def error_count(self) -> int:
        return len(self.all_errors)


class FeaturePipeline:
    """
    Composable feature engineering pipeline.

    Runs stages in sequence:
    1. Feature Builder (custom derived features)
    2. Window Features (time-window aggregations)
    3. Aggregations (grouped streaming aggregations)

    Each stage can be enabled/disabled independently.
    Pipeline stops on first failure if strict_mode=True.
    """

    def __init__(
        self,
        feature_builder: FeatureBuilder | None = None,
        window_extractor: WindowFeatureExtractor | None = None,
        aggregation_engine: AggregationEngine | None = None,
        strict_mode: bool = False,
    ) -> None:
        """
        Initialize pipeline.

        Args:
            feature_builder: FeatureBuilder instance (or None to skip)
            window_extractor: WindowFeatureExtractor instance (or None to skip)
            aggregation_engine: AggregationEngine instance (or None to skip)
            strict_mode: If True, stop on first feature engineering failure
        """
        self.feature_builder = feature_builder
        self.window_extractor = window_extractor
        self.aggregation_engine = aggregation_engine
        self.strict_mode = strict_mode

        self._stats = {
            "total_rows": 0,
            "valid_rows": 0,
            "rejected_rows": 0,
            "stage_stats": {},
        }

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "FeaturePipeline":
        """
        Create pipeline from configuration dict.

        Expected config structure:
        {
            "feature_builder": {"enabled": true, "features": [...], "safe_mode": true},
            "window_features": {"enabled": true, "configs": [...]},
            "aggregations": {"enabled": true, "configs": [...]},
            "strict_mode": false
        }
        """
        feature_builder = None
        if config.get("feature_builder", {}).get("enabled", False):
            fb_cfg = config["feature_builder"]
            features = []
            for feat_cfg in fb_cfg.get("features", []):
                features.append(FeatureDefinition(**feat_cfg))
            feature_builder = FeatureBuilder(
                feature_definitions=features,
                safe_mode=fb_cfg.get("safe_mode", True),
            )

        window_extractor = None
        if config.get("window_features", {}).get("enabled", False):
            wf_cfg = config["window_features"]
            configs = []
            for wc_cfg in wf_cfg.get("configs", []):
                from app.features.window_features import WindowConfig, WindowType, WindowAggregation
                configs.append(WindowConfig(
                    name=wc_cfg["name"],
                    source_field=wc_cfg["source_field"],
                    time_field=wc_cfg["time_field"],
                    window_type=WindowType(wc_cfg.get("window_type", "sliding")),
                    window_size=wc_cfg.get("window_size"),
                    slide_size=wc_cfg.get("slide_size"),
                    aggregations=[WindowAggregation(a) for a in wc_cfg.get("aggregations", ["count", "mean"])],
                    group_by=wc_cfg.get("group_by"),
                    watermark_delay=wc_cfg.get("watermark_delay"),
                ))
            window_extractor = WindowFeatureExtractor(configs=configs)

        aggregation_engine = None
        if config.get("aggregations", {}).get("enabled", False):
            agg_cfg = config["aggregations"]
            configs = []
            for ac_cfg in agg_cfg.get("configs", []):
                from app.features.aggregation import AggregationConfig, AggregationFunction
                configs.append(AggregationConfig(
                    name=ac_cfg["name"],
                    source_field=ac_cfg["source_field"],
                    group_by=ac_cfg.get("group_by", []),
                    functions=[AggregationFunction(f) for f in ac_cfg.get("functions", ["count", "mean"])],
                    time_field=ac_cfg.get("time_field"),
                    window=ac_cfg.get("window"),
                    emit_on_change=ac_cfg.get("emit_on_change", False),
                ))
            aggregation_engine = AggregationEngine(configs=configs)

        return cls(
            feature_builder=feature_builder,
            window_extractor=window_extractor,
            aggregation_engine=aggregation_engine,
            strict_mode=config.get("strict_mode", False),
        )

    def process(self, row: dict[str, Any], row_index: int = 0) -> FeaturePipelineResult:
        """
        Run all enabled feature engineering stages on a single row.

        Returns aggregated FeaturePipelineResult.
        """
        self._stats["total_rows"] += 1
        current_row = dict(row)
        all_errors = []
        warnings = []

        # Stage 1: Feature Builder
        builder_result = None
        if self.feature_builder:
            builder_result = self.feature_builder.build(current_row, row_index)
            if not builder_result.is_valid:
                all_errors.extend([{**e, "stage": "feature_builder"} for e in builder_result.errors])
                if self.strict_mode:
                    return self._make_result(False, row_index, row, None, builder_result=builder_result, errors=all_errors)
            else:
                current_row = builder_result.enhanced_row
                if builder_result.new_features:
                    warnings.append({
                        "stage": "feature_builder",
                        "message": f"Built features: {list(builder_result.new_features.keys())}",
                        "features": list(builder_result.new_features.keys()),
                    })

        # Stage 2: Window Features
        window_result = None
        if self.window_extractor:
            window_result = self.window_extractor.extract(current_row, row_index)
            if not window_result.is_valid:
                all_errors.extend([{**e, "stage": "window_features"} for e in window_result.errors])
                if self.strict_mode:
                    return self._make_result(False, row_index, row, None,
                        builder_result=builder_result, window_result=window_result, errors=all_errors, warnings=warnings)
            else:
                current_row = window_result.enhanced_row
                if window_result.window_features:
                    warnings.append({
                        "stage": "window_features",
                        "message": f"Extracted window features: {list(window_result.window_features.keys())}",
                        "features": list(window_result.window_features.keys()),
                    })

        # Stage 3: Aggregations
        aggregation_result = None
        if self.aggregation_engine:
            aggregation_result = self.aggregation_engine.aggregate(current_row, row_index)
            if not aggregation_result.is_valid:
                all_errors.extend([{**e, "stage": "aggregations"} for e in aggregation_result.errors])
                if self.strict_mode:
                    return self._make_result(False, row_index, row, None,
                        builder_result=builder_result, window_result=window_result,
                        aggregation_result=aggregation_result, errors=all_errors, warnings=warnings)
            else:
                current_row = aggregation_result.enhanced_row
                if aggregation_result.aggregation_results:
                    warnings.append({
                        "stage": "aggregations",
                        "message": f"Computed aggregations: {list(aggregation_result.aggregation_results.keys())}",
                        "features": list(aggregation_result.aggregation_results.keys()),
                    })

        is_valid = len(all_errors) == 0
        final_row = current_row if is_valid else None

        if is_valid:
            self._stats["valid_rows"] += 1
        else:
            self._stats["rejected_rows"] += 1

        return self._make_result(is_valid, row_index, row, final_row,
            builder_result=builder_result, window_result=window_result,
            aggregation_result=aggregation_result, errors=all_errors, warnings=warnings)

    def _make_result(
        self,
        is_valid: bool,
        row_index: int,
        original_row: dict[str, Any],
        final_row: dict[str, Any] | None,
        builder_result: FeatureResult | None = None,
        window_result: WindowResult | None = None,
        aggregation_result: AggregationResult | None = None,
        errors: list[dict[str, Any]] | None = None,
        warnings: list[dict[str, Any]] | None = None,
    ) -> FeaturePipelineResult:
        """Create FeaturePipelineResult from components."""
        return FeaturePipelineResult(
            is_valid=is_valid,
            row_index=row_index,
            original_row=original_row,
            final_row=final_row,
            builder_result=builder_result,
            window_result=window_result,
            aggregation_result=aggregation_result,
            all_errors=errors or [],
            warnings=warnings or [],
        )

    def process_batch(self, rows: list[dict[str, Any]]) -> list[FeaturePipelineResult]:
        """Process a batch of rows."""
        return [self.process(row, i) for i, row in enumerate(rows)]

    def get_valid_rows(self, results: list[FeaturePipelineResult]) -> list[dict[str, Any]]:
        """Extract valid enhanced rows."""
        return [r.final_row for r in results if r.is_valid and r.final_row]

    def get_stats(self) -> dict[str, Any]:
        """Get pipeline statistics."""
        stats = dict(self._stats)
        if stats["total_rows"] > 0:
            stats["success_rate"] = stats["valid_rows"] / stats["total_rows"]

        # Add stage-specific stats
        if self.feature_builder:
            stats["feature_builder"] = self.feature_builder.get_stats()
        if self.window_extractor:
            stats["window_features"] = self.window_extractor.get_stats()
        if self.aggregation_engine:
            stats["aggregations"] = self.aggregation_engine.get_stats()

        return stats

    def reset(self) -> None:
        """Reset all feature engineering stages and statistics."""
        self._stats = {
            "total_rows": 0,
            "valid_rows": 0,
            "rejected_rows": 0,
            "stage_stats": {},
        }
        if self.feature_builder:
            self.feature_builder.reset_stats()
        if self.window_extractor:
            self.window_extractor.reset()
        if self.aggregation_engine:
            self.aggregation_engine.reset()
        logger.info("Feature pipeline reset")

    def update_config(self, config: dict[str, Any]) -> None:
        """Update pipeline configuration at runtime."""
        if "feature_builder" in config and self.feature_builder:
            self.feature_builder.update_config(config["feature_builder"])
        if "window_features" in config and self.window_extractor:
            self.window_extractor.update_config(config["window_features"])
        if "aggregations" in config and self.aggregation_engine:
            self.aggregation_engine.update_config(config["aggregations"])
        if "strict_mode" in config:
            self.strict_mode = config["strict_mode"]
        logger.info("Feature pipeline config updated")