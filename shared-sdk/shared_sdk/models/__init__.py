"""
Shared Pydantic models for ASLP services.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class EventType(str, Enum):
    """Standard event types for streaming data."""
    DATA_POINT = "data_point"
    BATCH = "batch"
    CONTROL = "control"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class StreamMessage(BaseModel):
    """Standard message format for streaming data."""
    stream_id: str = Field(..., description="Unique stream identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    source: str = Field(..., description="Data source identifier")
    event_type: EventType = Field(default=EventType.DATA_POINT, description="Event type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Payload data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ModelState(BaseModel):
    """Model state for persistence."""
    model_name: str = Field(..., description="Model identifier")
    state: Dict[str, Any] = Field(..., description="Model state dictionary")
    version: int = Field(default=1, ge=1, description="State version")
    saved_at: datetime = Field(default_factory=datetime.utcnow, description="Save timestamp")
    metadata: Optional[Dict[str, Any]] = None


class ModelMetadata(BaseModel):
    """Model metadata for registry."""
    name: str = Field(..., description="Model name")
    class_path: str = Field(..., description="Python class path (e.g., river.tree.HoeffdingTreeClassifier)")
    hyperparameters: Dict[str, Any] = Field(default_factory=dict, description="Model hyperparameters")
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PredictionResult(BaseModel):
    """Single prediction result."""
    prediction: Any = Field(..., description="Prediction value")
    probability: Optional[Dict[Any, float]] = None
    features: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = Field(..., description="Prediction latency in ms")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LearningResult(BaseModel):
    """Single learning step result."""
    loss: Optional[float] = None
    metric_updates: Dict[str, float] = Field(default_factory=dict)
    latency_ms: float = Field(..., description="Learning latency in ms")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EvaluationResult(BaseModel):
    """Model evaluation result."""
    metrics: Dict[str, float] = Field(..., description="Evaluation metrics")
    sample_count: int = Field(..., ge=0, description="Number of samples evaluated")
    window_size: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DriftAlert(BaseModel):
    """Drift detection alert."""
    detector: str = Field(..., description="Drift detector name")
    drift_score: float = Field(..., description="Drift score")
    threshold: float = Field(..., description="Alert threshold")
    is_drift: bool = Field(..., description="Whether drift detected")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)


class ServiceRegistration(BaseModel):
    """Service registration info."""
    service_name: str
    base_url: str
    health_endpoint: str = "/api/v1/health"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    registered_at: datetime = Field(default_factory=datetime.utcnow)


class ServiceConfig(BaseModel):
    """Service configuration from Config Service."""
    service: str
    config: Dict[str, Any]
    version: int = 1
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ExperimentRecord(BaseModel):
    """Experiment tracking record."""
    experiment_id: str = Field(..., description="Unique experiment ID")
    name: str = Field(..., description="Experiment name")
    model_name: str = Field(..., description="Model used")
    config: Dict[str, Any] = Field(default_factory=dict, description="Experiment config")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Final metrics")
    status: str = Field(default="running", description="running, completed, failed")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)