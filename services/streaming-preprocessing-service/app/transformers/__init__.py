"""
Transformers Package - Data transformation modules for preprocessing pipeline.

Exports:
- DataCleaner: Removes invalid/outlier data
- Encoder: Categorical encoding (label, one-hot, ordinal)
- Normalizer: Feature scaling (min-max, z-score, robust)
- TypeConverter: Data type conversion
- TransformationPipeline: Composable transformation pipeline
"""

from app.transformers.data_cleaner import DataCleaner, CleanResult, CleanRule, CleanAction
from app.transformers.encoder import Encoder, EncodingStrategy, EncodingResult
from app.transformers.normalizer import Normalizer, NormalizationStrategy, NormalizationResult
from app.transformers.type_converter import TypeConverter, TypeConversionResult, TargetType
from app.transformers.pipeline import TransformationPipeline, TransformationResult

__all__ = [
    "DataCleaner",
    "CleanResult",
    "CleanRule",
    "CleanAction",
    "Encoder",
    "EncodingStrategy",
    "EncodingResult",
    "Normalizer",
    "NormalizationStrategy",
    "NormalizationResult",
    "TypeConverter",
    "TypeConversionResult",
    "TargetType",
    "TransformationPipeline",
    "TransformationResult",
]