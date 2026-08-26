"""
Constants for ASLP services.
"""

from enum import Enum


class ServiceName(str, Enum):
    """Standard service names."""
    CONFIGURATION = "configuration-service"
    STREAMING_PREPROCESSING = "streaming-preprocessing-service"
    MESSAGE_BROKER = "message-broker"
    ONLINE_ML_ENGINE = "online-ml-engine"
    STATE_STORE = "state-store"
    STORAGE_LAYER = "storage-layer"
    MONITORING_DASHBOARD = "monitoring-dashboard"


class LogLevel(str, Enum):
    """Standard log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HTTPStatus(int, Enum):
    """Standard HTTP status codes."""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class DefaultTimeout:
    """Default timeout values in seconds."""
    SHORT = 5.0
    MEDIUM = 30.0
    LONG = 60.0
    VERY_LONG = 300.0


class APIVersion(str, Enum):
    """API versions."""
    V1 = "v1"


class APIPrefix:
    """API path prefixes."""
    V1 = "/api/v1"


class DefaultPorts:
    """Default service ports."""
    CONFIGURATION = 8001
    STREAMING_PREPROCESSING = 8002
    MESSAGE_BROKER = 8003
    ONLINE_ML_ENGINE = 8004
    STATE_STORE = 8005
    STORAGE_LAYER = 8006
    MONITORING_DASHBOARD = 8501
    RABBITMQ = 5672
    RABBITMQ_MGMT = 15672


class StreamDefaults:
    """Default streaming configuration."""
    BATCH_SIZE = 1
    PREFETCH_COUNT = 100
    POLLING_INTERVAL = 1.0  # seconds
    RECONNECT_DELAY = 5.0  # seconds


class StateDefaults:
    """Default state management configuration."""
    AUTO_SAVE_INTERVAL = 300  # seconds
    MAX_VERSIONS = 10
    COMPRESSION = True


class StorageDefaults:
    """Default storage configuration."""
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    DEFAULT_COLLECTION = "experiments"


class MonitoringDefaults:
    """Default monitoring configuration."""
    REFRESH_INTERVAL = 5  # seconds
    MAX_DATA_POINTS = 1000
    ALERT_THRESHOLD_CPU = 80  # percent
    ALERT_THRESHOLD_MEMORY = 85  # percent


class RetryDefaults:
    """Default retry configuration."""
    MAX_ATTEMPTS = 3
    BASE_DELAY = 1.0  # seconds
    MAX_DELAY = 30.0  # seconds
    EXPONENTIAL_BASE = 2.0


class CircuitBreakerDefaults:
    """Default circuit breaker configuration."""
    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT = 30  # seconds


class ModelDefaults:
    """Default model configuration."""
    DEFAULT_LEARNING_RATE = 0.01
    DEFAULT_BATCH_SIZE = 1


class ValidationDefaults:
    """Default validation configuration."""
    MAX_STRING_LENGTH = 1000
    MAX_LIST_LENGTH = 10000
    MAX_DICT_DEPTH = 10