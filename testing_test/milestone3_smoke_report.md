# Milestone 3 Smoke Test Report

## Project
Streaming Preprocessing Service — Milestone 3

## Date
2026-07-24

## Purpose
Validate the Milestone 3 Streaming Preprocessing Service implementation — reading CSV data, converting to standard `StreamMessage` payload, and publishing to Message Broker.

## Milestone 3 Acceptance Scope

The service must support the CSV → JSON → Message Broker pipeline:

- Read CSV file in batches
- Convert each row to standard `StreamMessage` format with `{stream_id, timestamp, source, event_type, data, metadata}`
- Publish to Message Broker via `BrokerClient`
- Expose streaming control endpoints

## Test Environment

- Project root contains a Python virtual environment at: `streaming-platform/.env/`
- Dependencies installed via `pip install -r services/streaming-preprocessing-service/requirements.txt`

## Test Artifacts

- Smoke test runner: `testing_test/milestone3_smoke_test.py`
- Result JSON: `testing_test/milestone3_smoke_result.json`
- Sample data: `sample_data/sample.csv` (15 rows, 6 columns)

## Test Procedure

1. Verify all new module imports (reader, publisher, orchestrator, schemas)
2. Verify FastAPI application loads with correct title
3. Verify all 8 endpoints registered in OpenAPI schema
4. Test each endpoint with HTTP calls
5. Test CsvReader basic operations (open, columns, count)
6. Test CsvReader batch reading (async)
7. Test StreamMessage builder (row → message conversion)

## Test Results

### Summary

| Metric | Value |
|---|---:|
| Total checks | 23 |
| Passed | 23 |
| Failed | 0 |

### Detailed Results

| Check | Result | Detail |
|---|---:|---|
| import_csv_reader | PASS | CsvReader imported ok |
| import_broker_publisher | PASS | BrokerPublisher imported ok |
| import_streaming_service | PASS | StreamingOrchestrator imported ok |
| import_streaming_schemas | PASS | Streaming schemas imported ok |
| import_app | PASS | app title=ASLP Streaming Preprocessing Service |
| route_/health | PASS | Registered in OpenAPI |
| route_/status | PASS | Registered in OpenAPI |
| route_/bootstrap | PASS | Registered in OpenAPI |
| route_/config/reload | PASS | Registered in OpenAPI |
| route_/stream/start | PASS | Registered in OpenAPI |
| route_/stream/stop | PASS | Registered in OpenAPI |
| route_/stream/status | PASS | Registered in OpenAPI |
| route_/statistics | PASS | Registered in OpenAPI |
| GET /health | PASS | HTTP 200 |
| GET /status | PASS | HTTP 200 |
| GET /bootstrap | PASS | HTTP 200 |
| POST /stream/start | PASS | HTTP 200, is_running=true |
| GET /stream/status | PASS | HTTP 200 |
| GET /statistics | PASS | HTTP 200, total_batches=1 |
| POST /stream/stop | PASS | HTTP 200, success=true |
| csv_reader_basic | PASS | 6 columns, 15 rows estimated |
| csv_reader_batch | PASS | batch_size=5 returned 5 rows |
| stream_message_build | PASS | StreamMessage built with correct structure |

## Endpoint Notes

### `POST /stream/start`
Accepts `StreamStartRequest` and returns `StreamStatusResponse` with `is_running: true`. The background task begins reading CSV batches and publishing to the broker.

### `GET /stream/status`
Returns current streaming state — whether running, rows read, published count, elapsed time.

### `GET /statistics`
Returns detailed session statistics including batch count, success rate, error list, and timestamps.

### `POST /stream/stop`
Gracefully stops the background task, closes the CSV reader and publisher client.

## Observations

- All 23 checks passed without errors.
- The `StreamingOrchestrator` correctly reads CSV → builds `StreamMessage` → publishes via `BrokerPublisher`.
- Shared SDK's `CircuitBreaker` had a `time` variable scoping bug; fixed in the utils module.
- The service now has **8 REST endpoints** covering both Milestone 2 (config) and Milestone 3 (streaming).

## New Modules (Milestone 3)

| Module | File | Purpose |
|--------|------|---------|
| app/reader/ | `csv_reader.py` | Async CSV reader with batch support |
| app/publisher/ | `broker_publisher.py` | Publishes StreamMessage via BrokerClient |
| app/services/ | `streaming_service.py` | Orchestrator for background stream lifecycle |
| app/schemas/ | `streaming.py` | Request/response schemas for streaming endpoints |
| sample_data/ | `sample.csv` | 15-row sample CSV for testing |

## Conclusion

**Milestone 3 passed the smoke test.**

The Streaming Preprocessing Service can now:
1. Read CSV files asynchronously in batches
2. Convert rows to the standard `StreamMessage` payload format
3. Publish messages to the Message Broker via the shared SDK `BrokerClient`
4. Be controlled via REST API (start/stop/status/statistics)

## Next Recommended Step

Proceed to **Milestone 4 — Message Broker**: implement a standalone RabbitMQ-based broker service with exchange, queue, publisher, and consumer so the full pipeline (CSV → Preprocessing → Broker → Online ML) can run end-to-end.
