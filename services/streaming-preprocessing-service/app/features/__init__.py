"""
Features Package - Feature engineering modules for preprocessing pipeline.

Exports:
- FeatureBuilder: Custom feature creation from raw fields
- WindowFeatureExtractor: Time-window based feature extraction
- AggregationEngine: Streaming aggregations
- FeaturePipeline: Composable feature engineering pipeline
"""

from app.features.feature_builder import FeatureBuilder, FeatureDefinition, FeatureResult
from app.features.window_features import WindowFeatureExtractor, WindowConfig, WindowResult, WindowType, WindowAggregation
from app.features.aggregation import AggregationEngine, AggregationConfig, AggregationResult, AggregationFunction
from app.features.pipeline import FeaturePipeline, FeaturePipelineResult

__all__ = [
    "FeatureBuilder",
    "FeatureDefinition",
    "FeatureResult",
    "WindowFeatureExtractor",
    "WindowConfig",
    "WindowResult",
    "WindowType",
    "WindowAggregation",
    "AggregationEngine",
    "AggregationConfig",
    "AggregationResult",
    "AggregationFunction",
    "FeaturePipeline",
    "FeaturePipelineResult",
]