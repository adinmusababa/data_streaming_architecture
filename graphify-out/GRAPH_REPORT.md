# Graph Report - .  (2026-07-24)

## Corpus Check
- Corpus is ~29,079 words - fits in a single context window. You may not need a graph.

## Summary
- 809 nodes · 1264 edges · 75 communities (45 shown, 30 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 49 edges (avg confidence: 0.75)
- Token cost: 10,565 input · 1,456 output

## Community Hubs (Navigation)
- Configuration Service API
- Configuration Service Core & Database
- SDK Configuration Cache & Loader
- SDK Error & JSON Logger
- Stream Preprocessing Service API
- SDK Base HTTP Client
- Architecture Principles & Concepts
- SDK Constants & Enums
- Preprocessing Config Service
- SDK Data Models
- SDK Exceptions & Helpers
- SDK Exception Hierarchy
- SDK Schemas & Pagination
- Architecture Diagram
- SDK Response Models
- Config Service Documentation
- Service Client Rationales
- SDK Validators
- Client Factory Methods
- OnlineML Client
- REST API Specification
- State Store & Online ML
- Stream Preprocessing Pipeline
- Monitoring Dashboard
- Online ML Engine
- Storage Layer Adapters
- Streaming Preprocessing Client
- Exception Init Hierarchy
- Shared SDK Docs
- Broker Client
- System Overview Document
- Online ML Document Rationales
- Dev Dependencies
- Architecture Design
- Message Broker Document
- Configuration Service CLI
- SDK Response Rationales
- SDK Config Rationales
- Development Roadmap Document
- SDK Logger Rationales
- SDK Exceptions Rationales
- SDK Validator Init
- System Warning Document
- Preprocessing Doc Rationales
- Online ML Resources
- SDK Models Rationale
- Run Scripts
- Install Script
- Stop Scripts
- SDK Clean Script
- Config Service Model Init
- Config Service Repo Init
- Config Service Utils
- Config Service Schema Init
- Config Service Api Init
- Config Service Route Init
- Config Service Main
- Preprocessing Main
- Preprocessing Core Init
- Preprocessing Schema Init
- Preprocessing Service Init
- Preprocessing App Init
- Config Service Init
- Smoke Test Result
- Shared SDK Package Init
- SDK Schemas Rationale
- Base Requirements
- Dev Requirements
- Prod Requirements
- Load Test Plans
- Production Requirements
- Base Requirements File
- Dev Requirements File

## God Nodes (most connected - your core abstractions)
1. `BaseClient` - 32 edges
2. `ClientConfig` - 22 edges
3. `Adaptive Data Streaming Platform for Online Machine Learning` - 22 edges
4. `ConfigurationService` - 20 edges
5. `SystemLogger` - 18 edges
6. `ConfigLoader` - 17 edges
7. `APIException` - 17 edges
8. `StorageClient` - 16 edges
9. `RESTAPIConvention` - 16 edges
10. `StreamingConfigService` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Adaptive Stream Learning Platform (ASLP)` --semantically_similar_to--> `Adaptive Data Streaming Platform for Online Machine Learning`  [INFERRED] [semantically similar]
  streaming-platform/docs/01-System-Overview.md → README.md
- `Service Isolation` --semantically_similar_to--> `Service Independence`  [INFERRED] [semantically similar]
  streaming-platform/docs/01-System-Overview.md → README.md
- `API First` --rationale_for--> `Adaptive Data Streaming Platform for Online Machine Learning`  [EXTRACTED]
  streaming-platform/docs/01-System-Overview.md → README.md
- `Configuration First` --rationale_for--> `Adaptive Data Streaming Platform for Online Machine Learning`  [EXTRACTED]
  streaming-platform/docs/01-System-Overview.md → README.md
- `High Cohesion` --rationale_for--> `Adaptive Data Streaming Platform for Online Machine Learning`  [EXTRACTED]
  streaming-platform/docs/01-System-Overview.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **ASLP Core Microservices Architecture** — readme_configuration_service, readme_streaming_preprocessing_service, readme_message_broker, readme_online_ml_engine, readme_state_store_service, readme_storage_layer, readme_monitoring_dashboard [EXTRACTED 1.00]
- **ASLP Architectural Layers** — streaming_platform_docs_02_architecture_management_layer, streaming_platform_docs_02_architecture_processing_layer, streaming_platform_docs_02_architecture_streaming_layer, streaming_platform_docs_02_architecture_intelligence_layer, streaming_platform_docs_02_architecture_persistence_layer, streaming_platform_docs_02_architecture_presentation_layer [EXTRACTED 1.00]
- **Streaming Data Pipeline** — streaming_platform_docs_05_streaming_preprocessing_service_streaming_preprocessing, streaming_platform_docs_06_message_broker_document, docs_07_online_ml_engine_state_store, streaming_platform_docs_08_state_store_online_ml_engine, streaming_platform_docs_09_storage_layer_online_ml_engine [EXTRACTED 1.00]
- **Online ML Ecosystem** — docs_07_online_ml_engine_state_store, docs_07_online_ml_engine_state_manager, docs_07_online_ml_engine_storage_client, streaming_platform_docs_08_state_store_online_ml_engine, streaming_platform_docs_09_storage_layer_online_ml_engine [EXTRACTED 1.00]
- **Configuration Dependency** — docs_07_online_ml_engine_conf_service, streaming_platform_docs_08_state_store_conf_service, streaming_platform_docs_09_storage_layer_conf_service, streaming_platform_docs_04_configuration_service_configuration_service [INFERRED 0.95]
- **MonitoringDashboardArchitecture** — streaming_platform_docs_10_monitoring_dashboard_monitoringdashboard, streaming_platform_docs_10_monitoring_dashboard_restclientlayer, streaming_platform_docs_10_monitoring_dashboard_dashboardpages, streaming_platform_docs_10_monitoring_dashboard_widgetmanager, streaming_platform_docs_10_monitoring_dashboard_visualization, streaming_platform_docs_10_monitoring_dashboard_sessionmanager, streaming_platform_docs_10_monitoring_dashboard_logger [EXTRACTED 1.00]
- **SharedSDKModules** — streaming_platform_docs_11_shared_sdk_sharedsdk, streaming_platform_docs_11_shared_sdk_sdkclients, streaming_platform_docs_11_shared_sdk_sdklogger, streaming_platform_docs_11_shared_sdk_sdkresponses, streaming_platform_docs_11_shared_sdk_sdkexceptions, streaming_platform_docs_11_shared_sdk_sdkvalidators, streaming_platform_docs_11_shared_sdk_sdkschemas, streaming_platform_docs_11_shared_sdk_sdkutils, streaming_platform_docs_11_shared_sdk_sdkconstants, streaming_platform_docs_11_shared_sdk_sdkconfiguration [EXTRACTED 1.00]
- **SDKClients** — streaming_platform_docs_11_shared_sdk_configurationclient, streaming_platform_docs_11_shared_sdk_streamingclient, streaming_platform_docs_11_shared_sdk_brokerclient, streaming_platform_docs_11_shared_sdk_onlinemlclient, streaming_platform_docs_11_shared_sdk_statestoreclient, streaming_platform_docs_11_shared_sdk_storageclient [EXTRACTED 1.00]
- **SDKExceptionHierarchy** — streaming_platform_docs_11_shared_sdk_validationexception, streaming_platform_docs_11_shared_sdk_storageexception, streaming_platform_docs_11_shared_sdk_stateexception, streaming_platform_docs_11_shared_sdk_apiexception, streaming_platform_docs_11_shared_sdk_configurationexception [EXTRACTED 1.00]
- **RESTAPIStandards** — streaming_platform_docs_12_rest_api_specification_restapiconvention, streaming_platform_docs_12_rest_api_specification_apiversioning, streaming_platform_docs_12_rest_api_specification_resourcenaming, streaming_platform_docs_12_rest_api_specification_standardresponse, streaming_platform_docs_12_rest_api_specification_httpstatuscodes, streaming_platform_docs_12_rest_api_specification_heathendpoint [EXTRACTED 1.00]
- **BaseDependencies** — streaming_platform_requirements_base_fastapi, streaming_platform_requirements_base_pydantic, streaming_platform_requirements_base_httpx, streaming_platform_requirements_base_sqlalchemy, streaming_platform_requirements_base_uvicorn [EXTRACTED 1.00]
- **Shared SDK Client Suite** — streaming_platform_shared_sdk_readme_configurationclient, streaming_platform_shared_sdk_readme_statestoreclient, streaming_platform_shared_sdk_readme_baseclient, streaming_platform_shared_sdk_readme_circuitbreaker [INFERRED 0.85]
- **ASLP Foundation Stack** — streaming_platform_services_configuration_service_readme_configurationservice, streaming_platform_services_streaming_preprocessing_service_readme_streamingpreprocessingservice, streaming_platform_shared_sdk_readme_sharedsdk [INFERRED 0.85]

## Communities (75 total, 30 thin omitted)

### Community 0 - "Configuration Service API"
Cohesion: 0.07
Nodes (40): delete_config(), get_configs(), get_configuration_service(), health(), put_config(), AsyncSession, REST API routes for the Configuration Service., Delete a configuration entry. (+32 more)

### Community 1 - "Configuration Service Core & Database"
Cohesion: 0.07
Nodes (30): DeclarativeBase, get_settings(), BaseSettings, Application settings for the Configuration Service., Environment-driven application settings., Settings, close_db(), get_session() (+22 more)

### Community 2 - "SDK Configuration Cache & Loader"
Cohesion: 0.08
Nodes (23): ConfigCache, ConfigLoader, ConfigurationClient, load_service_config(), Any, Background polling loop., Fetch latest configuration from service., Get configuration value (from cache). (+15 more)

### Community 3 - "SDK Error & JSON Logger"
Cohesion: 0.08
Nodes (14): LogRecord, ErrorLogger, JSONFormatter, Any, Exception, Main logger class for ASLP services.      Features:     - JSON structured loggin, Internal log method with extra fields., Log exception with traceback. (+6 more)

### Community 4 - "Stream Preprocessing Service API"
Cohesion: 0.10
Nodes (26): bootstrap(), get_config_service(), health(), Minimal API routes for Streaming Preprocessing Service., reload_config(), status(), create_app(), lifespan() (+18 more)

### Community 5 - "SDK Base HTTP Client"
Cohesion: 0.12
Nodes (15): AsyncClient, Response, BaseClient, generate_request_id(), get_current_request_id(), Any, Build request keyword arguments., Execute HTTP request with retry and circuit breaker.          Args: (+7 more)

### Community 6 - "Architecture Principles & Concepts"
Cohesion: 0.08
Nodes (31): Adaptive Data Streaming Platform for Online Machine Learning, Configuration Service, Extensibility, High Configurability, Loose Coupling, Message Broker, Monitoring Dashboard, Online Machine Learning Engine (+23 more)

### Community 7 - "SDK Constants & Enums"
Cohesion: 0.08
Nodes (29): int, APIPrefix, APIVersion, CircuitBreakerDefaults, DefaultPorts, HTTPStatus, LogLevel, ModelDefaults (+21 more)

### Community 8 - "Preprocessing Config Service"
Cohesion: 0.12
Nodes (23): datetime, Configuration bootstrap for Streaming Preprocessing Service., Base HTTP client and service-specific clients for ASLP services.  Provides stand, Configuration client for Configuration Service.  Provides dynamic configuration, DefaultTimeout, Default timeout values in seconds., create_service_logger(), get_logger() (+15 more)

### Community 9 - "SDK Data Models"
Cohesion: 0.10
Nodes (26): DriftAlert, EvaluationResult, EventType, ExperimentRecord, LearningResult, ModelMetadata, ModelState, PredictionResult (+18 more)

### Community 10 - "SDK Exceptions & Helpers"
Cohesion: 0.10
Nodes (23): Raised when request validation fails., ValidationException, Shared SDK for Adaptive Stream Learning Platform (ASLP).  A common library provi, Set log level for all registered loggers., set_global_level(), generate_uuid(), merge_dicts(), Truncate string to max length. (+15 more)

### Community 11 - "SDK Exception Hierarchy"
Cohesion: 0.12
Nodes (21): APIException, ConfigurationException, ConflictException, ForbiddenException, NotFoundException, Exception, Standard exception hierarchy for ASLP services., Base exception for all API errors. (+13 more)

### Community 12 - "SDK Schemas & Pagination"
Cohesion: 0.13
Nodes (21): BaseRequest, BaseResponse, Config, ConfigurationResponse, HealthResponse, Metadata, PaginationParams, BaseModel (+13 more)

### Community 13 - "Architecture Diagram"
Cohesion: 0.10
Nodes (21): Apache Flink, Apache Kafka, API, Arsitektur Platform Data Streaming Infrastruktur, Configuration Service, Data Lake, Data Streaming Pipeline (end-to-end), Data Warehouse (+13 more)

### Community 14 - "SDK Response Models"
Cohesion: 0.11
Nodes (16): BaseResponse, Config, ErrorResponse, PaginatedResponse, BaseModel, T, Standard response models for all ASLP services., Base response model with common fields. (+8 more)

### Community 15 - "Config Service Documentation"
Cohesion: 0.12
Nodes (18): Async SQLAlchemy, Centralized Configuration, Configuration Service, PostgreSQL, Single Source of Truth, SQLite, CONFIG_SERVICE_URL, Streaming Preprocessing Service (+10 more)

### Community 16 - "Service Client Rationales"
Cohesion: 0.16
Nodes (9): Any, Client for Storage Layer service., Save a document to a collection., Find documents in a collection., Find a single document by ID., Count documents in a collection., List all collections., Get storage statistics. (+1 more)

### Community 17 - "SDK Validators"
Cohesion: 0.14
Nodes (10): BaseValidator, Any, Base validator class with common validation methods., Validate required field., Validate minimum string length., Validate maximum string length., Validate value is within range., Validate value is in allowed list. (+2 more)

### Community 18 - "Client Factory Methods"
Cohesion: 0.20
Nodes (12): Shared SDK client exports., create_broker_client(), create_online_ml_client(), create_state_store_client(), create_storage_client(), create_streaming_client(), Service-specific clients for ASLP services.  Each client provides a typed interf, Create and initialize broker client. (+4 more)

### Community 19 - "OnlineML Client"
Cohesion: 0.14
Nodes (7): OnlineMLClient, Client for Online ML Engine service., Get current model information., Get prediction history., Get learning statistics., Trigger manual state save., Trigger manual state load.

### Community 20 - "REST API Specification"
Cohesion: 0.15
Nodes (13): APIEndpointDefinition, APIFiltering, APILogging, APIPagination, APIVersioning, AuthenticationFuture, ConfigurationEndpoint, HealthEndpoint (+5 more)

### Community 21 - "State Store & Online ML"
Cohesion: 0.17
Nodes (12): Configuration Service, Configuration Service, Configuration Service, State Store (SAS-09), Metadata Manager, Model State, Repository, State Manager (+4 more)

### Community 22 - "Stream Preprocessing Pipeline"
Cohesion: 0.17
Nodes (12): Centralized Preprocessing, Data Cleaner, Configuration Client, Streaming Preprocessing Service (SAS-06), Feature Processor, Payload Builder, Publisher, Source Reader (+4 more)

### Community 23 - "Monitoring Dashboard"
Cohesion: 0.18
Nodes (11): DataStreamingMonitoringSystem, DashboardNoDirectDB, DashboardNoProcessing, DashboardPages, DashboardLogger, MonitoringDashboard, PollingStrategy, RESTClientLayer (+3 more)

### Community 24 - "Online ML Engine"
Cohesion: 0.18
Nodes (11): Broker Consumer, Online ML Engine (SAS-08), Evaluation Engine, Learning Engine, Message Broker, Model Lifecycle, Model Manager, Monitoring API (+3 more)

### Community 25 - "Storage Layer Adapters"
Cohesion: 0.18
Nodes (11): Storage Abstraction Layer, Adapter Manager, Storage Layer (SAS-10), Elasticsearch, MinIO, MongoDB, PostgreSQL, Redis (+3 more)

### Community 26 - "Streaming Preprocessing Client"
Cohesion: 0.18
Nodes (6): Client for Streaming Preprocessing Service., Start data streaming., Get preprocessing statistics., Get current preprocessing configuration., Reload preprocessing configuration., StreamingPreprocessingClient

### Community 28 - "Shared SDK Docs"
Cohesion: 0.20
Nodes (10): ConsistentImplementation, EasierMaintenance, ReduceCodeDuplication, SDKConfiguration, SDKConstants, SDKLogger, SDKSchemas, SDKUtils (+2 more)

### Community 29 - "Broker Client"
Cohesion: 0.20
Nodes (6): BrokerClient, Client for Message Broker service., Get queue information., Get exchange information., Get active connections., Publish a message to the broker.

### Community 30 - "System Overview Document"
Cohesion: 0.32
Nodes (8): Streaming Preprocessing Service, Asynchronous Communication, Message Broker (SAS-07), Exchange, Publisher Connection, Queue, Routing, Streaming Preprocessing Service

### Community 31 - "Online ML Document Rationales"
Cohesion: 0.38
Nodes (7): State Manager, State Store, Online ML Engine, State Store, Consumer Connection, Online ML Engine, Online ML Engine

### Community 32 - "Dev Dependencies"
Cohesion: 0.29
Nodes (7): Black, Mypy, Pytest, Ruff, FastAPI, Uvicorn, ProductionBase

### Community 33 - "Architecture Design"
Cohesion: 0.29
Nodes (7): Docker Configuration, Repository Structure (SAS-04), Microservice Independence, Monitoring Dashboard, Naming Convention, Repository Structure, Shared Module

### Community 34 - "Message Broker Document"
Cohesion: 0.29
Nodes (7): BrokerClient, ConfigurationClient, OnlineMLClient, SDKClients, StateStoreClient, StorageClient, StreamingClient

### Community 35 - "Configuration Service CLI"
Cohesion: 0.33
Nodes (5): get_settings(), BaseSettings, Application settings for Streaming Preprocessing Service., Settings, Core package for Streaming Preprocessing Service.

### Community 37 - "SDK Config Rationales"
Cohesion: 0.29
Nodes (3): Client for State Store service., List available states., StateStoreClient

### Community 38 - "Development Roadmap Document"
Cohesion: 0.33
Nodes (6): APIException, ConfigurationException, SDKExceptions, StateException, StorageException, ValidationException

### Community 39 - "SDK Logger Rationales"
Cohesion: 0.33
Nodes (3): CircuitBreaker, T, Simple circuit breaker implementation.

### Community 40 - "SDK Exceptions Rationales"
Cohesion: 0.33
Nodes (6): get_service_context(), Set global service context., Get current service context., Service-scoped context for logging., ServiceContext, set_service_context()

### Community 41 - "SDK Validator Init"
Cohesion: 0.33
Nodes (6): json_dumps(), json_loads(), Any, Safely get nested dictionary value., Serialize to JSON with default handlers., safe_get()

### Community 42 - "System Warning Document"
Cohesion: 0.40
Nodes (5): ErrorResponse, SDKResponses, SuccessResponse, StandardErrorResponse, StandardResponse

### Community 43 - "Preprocessing Doc Rationales"
Cohesion: 0.67
Nodes (4): Storage Client, Storage Layer, Storage Layer, Online ML Engine

### Community 44 - "Online ML Resources"
Cohesion: 0.50
Nodes (4): LogLevel, Enum, str, Log levels matching standard Python logging.

## Knowledge Gaps
- **123 isolated node(s):** `aslp-shared-sdk`, `Config`, `Config`, `Adaptive Stream Learning Platform (ASLP)`, `REST API Communication` (+118 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BaseClient` connect `SDK Base HTTP Client` to `SDK Configuration Cache & Loader`, `SDK Config Rationales`, `SDK Logger Rationales`, `Preprocessing Config Service`, `SDK Exceptions & Helpers`, `Service Client Rationales`, `Client Factory Methods`, `OnlineML Client`, `Streaming Preprocessing Client`, `Broker Client`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `ConfigurationService` connect `Configuration Service API` to `Configuration Service Core & Database`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `ConfigLoader` connect `SDK Configuration Cache & Loader` to `Stream Preprocessing Service API`, `SDK Base HTTP Client`, `SDK Response Rationales`, `Preprocessing Config Service`, `SDK Exceptions & Helpers`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `BaseClient` (e.g. with `BrokerClient` and `OnlineMLClient`) actually correct?**
  _`BaseClient` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `ClientConfig` (e.g. with `BrokerClient` and `OnlineMLClient`) actually correct?**
  _`ClientConfig` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aslp-shared-sdk`, `Config`, `Config` to the rest of the system?**
  _123 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Configuration Service API` be split into smaller, more focused modules?**
  _Cohesion score 0.07294117647058823 - nodes in this community are weakly interconnected._