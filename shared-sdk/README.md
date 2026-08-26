# ASLP Shared SDK

Shared library for the **Adaptive Stream Learning Platform (ASLP)**.

Provides common utilities, clients, and patterns used across all microservices in the platform.

## Features

- **HTTP Clients** - Standardized async clients for all platform services with retry, circuit breaker, and timeout handling
- **Structured Logging** - JSON-formatted logs with request/service context propagation
- **Configuration Management** - Dynamic config loading from Configuration Service with caching and polling
- **Common Schemas** - Standardized Pydantic models for requests, responses, and domain objects
- **Exception Hierarchy** - Consistent error handling across services
- **Utilities** - Retry decorators, circuit breaker, UUID generation, JSON helpers

## Installation

```bash
pip install -e ./shared-sdk
```

Or add to your service's `requirements.txt`:
```
aslp-shared-sdk @ file://../shared-sdk
```

## Quick Start

```python
from shared_sdk import (
    # Clients
    ConfigurationClient,
    StateStoreClient,
    StorageClient,
    OnlineMLClient,
    BrokerClient,
    StreamingPreprocessingClient,
    
    # Configuration
    ConfigLoader,
    
    # Logging
    SystemLogger,
    get_logger,
    
    # Models
    StreamMessage,
    ModelState,
    PredictionResult,
    
    # Utils
    retry,
    CircuitBreaker,
    generate_uuid,
)

# Example: Using a service client
async def example():
    async with StateStoreClient() as client:
        state = await client.load_state("my_model")
        print(state)

# Example: Structured logging
logger = get_logger("my-service", service_name="online-ml-engine")
logger.info("Model loaded", model="river_hoeffding_tree", version=3)
```

## Module Structure

```
shared_sdk/
├── clients/           # HTTP clients for all services
│   ├── base.py       # BaseClient with retry/circuit breaker
│   ├── configuration.py  # ConfigService client + ConfigLoader
│   └── services.py   # Typed clients for each platform service
├── logger/           # Structured logging
├── responses/        # Standard response models
├── exceptions/       # Exception hierarchy
├── schemas/          # Pydantic request/response schemas
├── models/           # Domain models (StreamMessage, ModelState, etc.)
├── utils/            # Utilities (retry, circuit breaker, etc.)
├── validators/       # Validation helpers
├── constants/        # Platform constants
└── configuration/    # Config loading utilities
```

## Key Components

### HTTP Clients

All service clients inherit from `BaseClient` which provides:
- Automatic retry with exponential backoff
- Circuit breaker pattern
- Request/response logging
- Standardized error handling
- Configurable timeouts

```python
async with StateStoreClient() as client:
    # Save model state
    await client.save_state(
        model_name="river_hoeffding_tree",
        state={"weights": {...}, "stats": {...}},
        metadata={"accuracy": 0.95},
    )
    
    # Load latest state
    state = await client.load_state("river_hoeffding_tree")
```

### Configuration Loading

```python
# One-time load
config = await load_service_config("online-ml-engine", defaults={"learning_rate": 0.01})

# Or with caching and polling
loader = ConfigLoader("online-ml-engine", poll_interval=30)
await loader.start()

# Get values from cache
learning_rate = loader.get("learning_rate", 0.01)

# Register change callback
loader.on_change(lambda config: print(f"Config updated: {config}"))

await loader.stop()
```

### Structured Logging

```python
logger = SystemLogger("my-service", service_name="online-ml-engine")

# Request logging
logger.request_start("req-123", "POST", "/api/v1/predict")
# ... process request ...
logger.request_end(200)

# Error logging
try:
    risky_operation()
except Exception as e:
    logger.request_error(e)
```

### Domain Models

```python
from shared_sdk.models import StreamMessage, EventType, ModelState, PredictionResult

# Streaming message
msg = StreamMessage(
    stream_id="sensor-001",
    source="kafka",
    event_type=EventType.DATA_POINT,
    data={"temperature": 25.3, "humidity": 60},
    metadata={"sensor_id": "temp-001"},
)

# Model state persistence
state = ModelState(
    model_name="river_hoeffding_tree",
    state={"tree": {...}, "metrics": {...}},
    version=5,
    metadata={"samples_seen": 10000},
)

# Prediction result
result = PredictionResult(
    prediction=1,
    probability={0: 0.2, 1: 0.8},
    features={"temp": 25.3, "humidity": 60},
    latency_ms=2.5,
)
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check --fix .

# Type check
mypy shared_sdk
```

## Architecture Integration

This SDK is designed to work with the ASLP microservices:

| Service | Port | Client |
|---------|------|--------|
| Configuration Service | 8001 | `ConfigurationClient` |
| Streaming Preprocessing | 8002 | `StreamingPreprocessingClient` |
| Message Broker | 8003 | `BrokerClient` |
| Online ML Engine | 8004 | `OnlineMLClient` |
| State Store | 8005 | `StateStoreClient` |
| Storage Layer | 8006 | `StorageClient` |
| Monitoring Dashboard | 8501 | - |

## Versioning

This SDK follows semantic versioning. Breaking changes will increment the major version.

## License

MIT