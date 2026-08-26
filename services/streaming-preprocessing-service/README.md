# Streaming Preprocessing Service

This service loads runtime configuration from the Configuration Service and uses only safe local defaults for startup.

## Current milestone scope

- Bootstrap the service
- Read configuration from Configuration Service
- Expose health/status/reload endpoints
- Avoid hardcoded runtime values for configurable settings

## Endpoints

- `GET /health`
- `GET /status`
- `POST /config/reload`
- `GET /bootstrap`

## Configuration source

The service reads from:

- `CONFIG_SERVICE_URL`
- `configuration-service` config payloads

## Run

```bash
python main.py
```
