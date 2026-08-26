# Milestone 2 Smoke Test Report

## Project
Configuration Service - Milestone 2

## Date
2026-07-23

## Purpose
Validate the Milestone 2 Configuration Service implementation against the original architecture plan.

The service is intended to be the first core service in the platform and the single source of truth for configuration so downstream services do not rely on hardcoded values.

## Milestone 2 Acceptance Scope

The service must expose the following minimal endpoints:

- `GET /config`
- `PUT /config`
- `POST /config/reload`
- `GET /health`
- `GET /status`

## Test Environment

- Project root contains a Python virtual environment at:

```text
streaming-platform/.env/
```

- Python executable used:

```text
streaming-platform/.env/Scripts/python.exe
```

- Dependencies were installed into that virtual environment using:

```bash
pip install -r services/configuration-service/requirements.txt
```

## Test Artifacts

### Smoke test runner
File:

```text
testing_test/milestone2_smoke_runner.py
```

### Raw smoke output
File:

```text
testing_test/milestone2_smoke_result.json
```

### Console log
File:

```text
testing_test/milestone2_smoke_output.log
```

## Test Procedure

### Step 1 - Verify the virtual environment
Confirmed that the project contains a Python 3.12 virtual environment in `.env/`.

### Step 2 - Install service dependencies
Installed the Configuration Service dependencies into the virtual environment.

### Step 3 - Run a structured smoke test
Executed a Python smoke runner that checked:

1. `fastapi` import
2. `sqlalchemy` import
3. Configuration Service app import
4. `GET /api/v1/health`
5. `GET /api/v1/status`
6. `GET /api/v1/config`
7. `PUT /api/v1/config`
8. `POST /api/v1/config/reload`

### Step 4 - Save the results
The smoke runner wrote the structured result to JSON, and this report was written from that result.

## Test Results

### Summary

| Metric | Value |
|---|---:|
| Total checks | 8 |
| Passed | 8 |
| Failed | 0 |

### Detailed Results

| Check | Result | Detail |
|---|---:|---|
| import_fastapi | PASS | fastapi import ok |
| import_sqlalchemy | PASS | sqlalchemy import ok |
| import_app | PASS | app title=ASLP Configuration Service |
| GET /api/v1/health | PASS | HTTP 200, service healthy |
| GET /api/v1/status | PASS | HTTP 200, status returned successfully |
| GET /api/v1/config | PASS | HTTP 200, returned 8 config items |
| PUT /api/v1/config | PASS | HTTP 200, configuration updated successfully |
| POST /api/v1/config/reload | PASS | HTTP 200, reload completed successfully |

## Endpoint Notes

### `GET /api/v1/health`
Returned a healthy service response:

- service: `configuration-service`
- status: `running`
- version: `1.0.0`
- database: `connected`

### `GET /api/v1/status`
Returned operational state successfully, including:

- total configurations
- cached configurations
- database status
- last reload time

### `GET /api/v1/config`
Returned the seeded platform configuration entries. The test confirmed that the Configuration Service already contains default values for the platform services.

### `PUT /api/v1/config`
Successfully updated `test-service` configuration and increased its version.

### `POST /api/v1/config/reload`
Successfully reloaded configuration cache and returned the number of loaded configs.

## Observations

- The Configuration Service now runs correctly in the Python 3.12 virtual environment.
- Default platform configs are seeded successfully.
- Core Milestone 2 endpoints are responding with HTTP 200.
- The service is now a workable configuration source for downstream services.

## Conclusion

**Milestone 2 passed the smoke test.**

The Configuration Service is now in a usable state as the first foundational service of the platform.
It can act as the central configuration source so future services can avoid hardcoded settings.

## Next Recommended Step

Proceed to connect downstream services to this Configuration Service so they read configuration dynamically instead of using local hardcoded defaults.
