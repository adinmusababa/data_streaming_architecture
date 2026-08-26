# Configuration Service

This service is the first foundation service in the ASLP platform.
It stores and serves configuration for every other service in the system.

## Purpose

- Centralized configuration storage
- Single source of truth for service settings
- No hardcoded configuration in downstream services

## Canonical Endpoints

- `GET /api/v1/config`
- `PUT /api/v1/config`
- `POST /api/v1/config/reload`
- `GET /api/v1/health`
- `GET /api/v1/status`

## Compatibility Aliases

For convenience during early development, root aliases are also available:

- `GET /config`
- `PUT /config`
- `POST /config/reload`
- `GET /health`
- `GET /status`

## Storage

The service uses an async SQLAlchemy storage layer.
A local SQLite database is used by default so the service runs immediately.
You can switch to PostgreSQL by setting `DATABASE_URL` in the environment.

## Run

```bash
python main.py
```
