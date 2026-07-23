"""
Shared SDK for Adaptive Stream Learning Platform (ASLP).

A common library providing:
- Standardized HTTP clients for inter-service communication
- Structured logging with context propagation
- Consistent response/exception schemas
- Configuration management
- Common utilities and validators
- Shared Pydantic models and schemas
"""

from shared_sdk.responses import (
    SuccessResponse,
    ErrorResponse,
    ValidationResponse,
    create_success_response,
    create_error_response,
)
from shared_sdk.exceptions import (
    ValidationException,
    ConfigurationException,
    StorageException,
    StateException,
    APIException,
    ServiceUnavailableException,
)
from shared_sdk.logger import (
    SystemLogger,
    get_logger,
    set_global_level,
    LogLevel,
    RequestContext,
    ServiceContext,
)
from shared_sdk.clients import (
    BaseClient,
    ConfigurationClient,
    StateStoreClient,
    StorageClient,
    BrokerClient,
    OnlineMLClient,
    StreamingClient,
    ClientConfig,
)
from shared_sdk.configuration import (
    ConfigLoader,
    load_service_config,
    ConfigCache,
)
from shared_sdk.utils import (
    generate_uuid,
    now_utc,
    json_dumps,
    json_loads,
    retry,
    CircuitBreaker,
    truncate_string,
    safe_get,
    merge_dicts,
)
from shared_sdk.validators import (
    BaseValidator,
    validate_model,
    required_validator,
    range_validator,
    one_of_validator,
    pattern_validator,
)
from shared_sdk.schemas import (
    BaseRequest,
    BaseResponse,
    PaginationParams,
    Metadata,
    HealthResponse,
    StatusResponse,
    StatisticsResponse,
    ConfigurationResponse,
    ReloadConfigRequest,
)
from shared_sdk.models import (
    StreamMessage,
    EventType,
    ModelState,
    ModelMetadata,
    PredictionResult,
    LearningResult,
    EvaluationResult,
    DriftAlert,
    ServiceRegistration,
    ServiceConfig,
    ExperimentRecord,
)
from shared_sdk.constants import (
    ServiceName,
    HTTPStatus,
    DefaultTimeout,
    APIVersion,
    APIPrefix,
    DefaultPorts,
    StreamDefaults,
    StateDefaults,
    StorageDefaults,
    MonitoringDefaults,
    RetryDefaults,
    CircuitBreakerDefaults,
)

__version__ = "0.1.0"

__all__ = [
    # Responses
    "SuccessResponse",
    "ErrorResponse",
    "ValidationResponse",
    "create_success_response",
    "create_error_response",
    # Exceptions
    "ValidationException",
    "ConfigurationException",
    "StorageException",
    "StateException",
    "APIException",
    "ServiceUnavailableException",
    # Logger
    "SystemLogger",
    "get_logger",
    "set_global_level",
    "LogLevel",
    "RequestContext",
    "ServiceContext",
    # Clients
    "BaseClient",
    "ConfigurationClient",
    "StateStoreClient",
    "StorageClient",
    "BrokerClient",
    "OnlineMLClient",
    "StreamingClient",
    "ClientConfig",
    # Configuration
    "ConfigLoader",
    "load_service_config",
    "ConfigCache",
    # Utils
    "generate_uuid",
    "now_utc",
    "json_dumps",
    "json_loads",
    "retry",
    "CircuitBreaker",
    "truncate_string",
    "safe_get",
    "merge_dicts",
    # Validators
    "BaseValidator",
    "validate_model",
    "required_validator",
    "range_validator",
    "one_of_validator",
    "pattern_validator",
    # Schemas
    "BaseRequest",
    "BaseResponse",
    "PaginationParams",
    "Metadata",
    "HealthResponse",
    "StatusResponse",
    "StatisticsResponse",
    "ConfigurationResponse",
    "ReloadConfigRequest",
    # Models
    "StreamMessage",
    "EventType",
    "ModelState",
    "ModelMetadata",
    "PredictionResult",
    "LearningResult",
    "EvaluationResult",
    "DriftAlert",
    "ServiceRegistration",
    "ServiceConfig",
    "ExperimentRecord",
    # Constants
    "ServiceName",
    "HTTPStatus",
    "DefaultTimeout",
    "APIVersion",
    "APIPrefix",
    "DefaultPorts",
    "StreamDefaults",
    "StateDefaults",
    "StorageDefaults",
    "MonitoringDefaults",
    "RetryDefaults",
    "CircuitBreakerDefaults",
]