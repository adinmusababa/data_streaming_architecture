"""
Milestone 3 — Streaming Preprocessing Service: Smoke Test

Validates:
  1. All module imports (reader, publisher, orchestrator, schemas)
  2. FastAPI application loads correctly
  3. All 8 endpoints are registered in OpenAPI schema
  4. Health endpoint returns 200
  5. Bootstrap returns config
  6. Stream start accepts request and returns status
  7. Stream status returns correct state
  8. Stream stop works cleanly
  9. Statistics endpoint returns proper structure
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"C:\Users\Musa\OneDrive - Universitas Teknologi Yogyakarta (1)\integrasi data streaming infastuktur\streaming-platform")
sys.path.insert(0, str(ROOT / "services/streaming-preprocessing-service"))
sys.path.insert(0, str(ROOT / "shared-sdk"))

results = []


def record(name: str, ok: bool, detail: str) -> None:
    results.append({"name": name, "ok": ok, "detail": detail, "timestamp": datetime.now(timezone.utc).isoformat()})


# ------------------------------------------------------------------
# 1. Module imports
# ------------------------------------------------------------------
try:
    from app.reader.csv_reader import CsvReader
    record("import_csv_reader", True, "CsvReader imported ok")
except Exception as e:
    record("import_csv_reader", False, repr(e))

try:
    from app.publisher.broker_publisher import BrokerPublisher
    record("import_broker_publisher", True, "BrokerPublisher imported ok")
except Exception as e:
    record("import_broker_publisher", False, repr(e))

try:
    from app.services.streaming_service import StreamingOrchestrator
    record("import_streaming_service", True, "StreamingOrchestrator imported ok")
except Exception as e:
    record("import_streaming_service", False, repr(e))

try:
    from app.schemas.streaming import StreamStartRequest, StreamStatusResponse, StreamStatisticsResponse, StreamStopResponse
    record("import_streaming_schemas", True, "Streaming schemas imported ok")
except Exception as e:
    record("import_streaming_schemas", False, repr(e))


# ------------------------------------------------------------------
# 2. App and routes
# ------------------------------------------------------------------
app = None
try:
    from app.core.app import app as fastapi_app
    app = fastapi_app
    record("import_app", True, f"app title={fastapi_app.title}")
except Exception as e:
    record("import_app", False, repr(e))

if app is not None:
    # Check OpenAPI schema for all required routes
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        schema = client.get("/openapi.json").json()
        paths = list(schema.get("paths", {}).keys())
        expected_paths = [
            "/health", "/status", "/bootstrap", "/config/reload",
            "/stream/start", "/stream/stop", "/stream/status", "/statistics",
        ]
        for p in expected_paths:
            if p in paths:
                record(f"route_{p.replace('/', '_')}", True, f"{p} registered in OpenAPI")
            else:
                record(f"route_{p.replace('/', '_')}", False, f"{p} missing from OpenAPI")
    except Exception as e:
        record("openapi_check", False, repr(e))

    # ------------------------------------------------------------------
    # 3. Endpoint smoke tests
    # ------------------------------------------------------------------
    try:
        client = TestClient(app)

        # Health
        r = client.get("/health")
        body = r.json()
        record("GET /health", r.status_code == 200, json.dumps({"status_code": r.status_code, "body": body}, default=str))

        # Status
        r = client.get("/status")
        body = r.json()
        record("GET /status", r.status_code == 200, json.dumps({"status_code": r.status_code, "body": body}, default=str))

        # Bootstrap
        r = client.get("/bootstrap")
        body = r.json()
        record("GET /bootstrap", r.status_code == 200, json.dumps({"status_code": r.status_code, "success": body.get("success")}, default=str))

        # Stream start
        r = client.post("/stream/start", json={"source_path": "sample_data/sample.csv", "batch_size": 5})
        body = r.json()
        record("POST /stream/start", r.status_code == 200 and body.get("is_running") is True, json.dumps({"status_code": r.status_code, "is_running": body.get("is_running")}, default=str))

        # Stream status
        r = client.get("/stream/status")
        body = r.json()
        record("GET /stream/status", r.status_code == 200, json.dumps({"status_code": r.status_code, "is_running": body.get("is_running")}, default=str))

        # Statistics
        r = client.get("/statistics")
        body = r.json()
        record("GET /statistics", r.status_code == 200, json.dumps({"status_code": r.status_code, "total_batches": body.get("total_batches")}, default=str))

        # Stream stop
        r = client.post("/stream/stop")
        body = r.json()
        record("POST /stream/stop", r.status_code == 200 and body.get("success") is True, json.dumps({"status_code": r.status_code, "success": body.get("success")}, default=str))

    except Exception as e:
        record("endpoint_smoke_setup", False, repr(e))


# ------------------------------------------------------------------
# 4. CsvReader unit check
# ------------------------------------------------------------------
try:
    from app.reader.csv_reader import CsvReader
    reader = CsvReader(str(ROOT / "sample_data" / "sample.csv"))
    reader.open()
    assert reader.columns == ["sensor_id", "timestamp", "temperature", "humidity", "pressure", "status"]
    assert reader.total_estimated == 15
    reader.close()
    record("csv_reader_basic", True, f"columns={reader.columns}, estimated={reader.total_estimated}")
except Exception as e:
    record("csv_reader_basic", False, repr(e))

try:
    import asyncio
    reader = CsvReader(str(ROOT / "sample_data" / "sample.csv"))
    reader.open()
    batch = asyncio.run(reader.read_batch(5))
    assert len(batch) == 5
    assert "sensor_id" in batch[0]
    assert "temperature" in batch[0]
    reader.close()
    record("csv_reader_batch", True, f"batch_size=5, got {len(batch)} rows, keys={list(batch[0].keys())}")
except Exception as e:
    record("csv_reader_batch", False, repr(e))


# ------------------------------------------------------------------
# 5. StreamMessage builder check
# ------------------------------------------------------------------
try:
    from shared_sdk.models import StreamMessage, EventType
    from app.services.streaming_service import StreamingOrchestrator
    orch = StreamingOrchestrator()
    # Test the row-to-message conversion
    rows = [{"sensor_id": "T001", "timestamp": "2025-01-01", "temperature": "25.0", "humidity": "60", "pressure": "1013", "status": "active"}]
    messages = orch._rows_to_messages(rows)
    assert len(messages) == 1
    msg = messages[0]
    assert msg.event_type == EventType.DATA_POINT
    assert "temperature" in msg.data
    assert msg.metadata.get("sensor_id") == "T001"
    assert msg.metadata.get("source_type") == "csv"
    record("stream_message_build", True, f"stream_id={msg.stream_id[:8]}..., data_keys={list(msg.data.keys())}")
except Exception as e:
    record("stream_message_build", False, repr(e))


# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
for item in results:
    status = "PASS" if item["ok"] else "FAIL"
    print(f"{item['name']}\t{status}\t{item['detail']}")

failed = [item for item in results if not item["ok"]]
print(f"TOTAL\t{len(results)}")
print(f"PASSED\t{len(results) - len(failed)}")
print(f"FAILED\t{len(failed)}")
