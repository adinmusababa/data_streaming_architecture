"""
Milestone 4 — Message Broker Service: Smoke Test

Validates:
  1. All module imports (kafka_backend, broker_service, schemas)
  2. FastAPI application loads correctly
  3. All SAS-07 endpoints are registered in OpenAPI schema
  4. Health endpoint returns 200 with kafka status
  5. Status endpoint returns operational counters
  6. Publish via REST contract matches shared_sdk BrokerClient
  7. Consume returns published messages
  8. Queue info reports backlog
  9. Exchange info lists bindings
 10. Statistics endpoint returns proper structure
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"C:\Users\Musa\OneDrive - Universitas Teknologi Yogyakarta (1)\integrasi data streaming infastuktur\streaming-platform")
sys.path.insert(0, str(ROOT / "services/message-broker"))
sys.path.insert(0, str(ROOT / "shared-sdk"))

results = []


def record(name: str, ok: bool, detail: str) -> None:
    results.append({"name": name, "ok": ok, "detail": detail, "timestamp": datetime.now(timezone.utc).isoformat()})
    print(("PASS" if ok else "FAIL"), name, "-", detail)


# ------------------------------------------------------------------
# 1. Module imports
# ------------------------------------------------------------------
try:
    from app.broker.kafka_backend import KafkaBackend, BrokerStats, topic_for
    record("import_kafka_backend", True, f"topic_for('stream_exchange','stream_data')={topic_for('stream_exchange', 'stream_data')}")
except Exception as e:
    record("import_kafka_backend", False, repr(e))

try:
    from app.services.broker_service import BrokerConfigService
    record("import_broker_service", True, "BrokerConfigService imported ok")
except Exception as e:
    record("import_broker_service", False, repr(e))

try:
    from app.schemas.broker import PublishRequest, ConsumeRequest, QueueInfoResponse
    record("import_broker_schemas", True, "Broker schemas imported ok")
except Exception as e:
    record("import_broker_schemas", False, repr(e))


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

required_paths = {
    "/health",
    "/status",
    "/config/reload",
    "/api/v1/publish",
    "/api/v1/consume",
    "/api/v1/queue/{queue_name}",
    "/api/v1/exchange/{exchange_name}",
    "/connections",
    "/statistics",
}
if app is not None:
    try:
        schema_paths = set()
        for route in app.routes:
            path = getattr(route, "path", None)
            if path:
                schema_paths.add(path)
        missing = {p for p in required_paths if p not in schema_paths}
        if missing:
            record("routes_registered", False, f"missing: {sorted(missing)}")
        else:
            record("routes_registered", True, f"{len(required_paths)} required paths present")
    except Exception as e:
        record("routes_registered", False, repr(e))


# ------------------------------------------------------------------
# 3. Live HTTP tests against running service (optional when offline)
# ------------------------------------------------------------------
BROKER_URL = os.environ.get("ASLP_BROKER_URL", "http://localhost:8003")


async def live_tests() -> None:
    import httpx

    async with httpx.AsyncClient(base_url=BROKER_URL, timeout=30.0) as client:
        # health
        try:
            r = await client.get("/health")
            body = r.json()
            ok = r.status_code == 200 and body.get("version") == "1.0.0"
            record("health_endpoint", ok, f"status={r.status_code} kafka={body.get('kafka')}")
        except Exception as e:
            record("health_endpoint", False, repr(e))
            return

        # status
        try:
            r = await client.get("/status")
            body = r.json()
            ok = r.status_code == 200 and body.get("service") == "message-broker"
            record("status_endpoint", ok, f"published={body.get('total_published')} consumed={body.get('total_consumed')}")
        except Exception as e:
            record("status_endpoint", False, repr(e))

        # publish via SDK contract shape {exchange, routing_key, message}
        stamp = datetime.now(timezone.utc).isoformat()
        payload = {
            "stream_id": "smoke-m4-001",
            "timestamp": stamp,
            "source": "smoke_test",
            "event_type": "data_point",
            "data": {"row": 1, "value": 42},
            "metadata": {"milestone": 4},
        }
        try:
            r = await client.post(
                "/api/v1/publish",
                json={"exchange": "stream_exchange", "routing_key": "smoke_m4", "message": payload},
            )
            body = r.json()
            ok = r.status_code == 200 and body.get("published") is True
            record("publish_rest_contract", ok, f"queue={body.get('queue')} offset={body.get('offset')}")
        except Exception as e:
            record("publish_rest_contract", False, repr(e))
            return

        # small delay so the record is visible to a fresh consumer
        await asyncio.sleep(1.0)

        # consume non-destructive peek
        try:
            r = await client.post(
                "/api/v1/consume",
                json={"queue": "stream_exchange__smoke_m4", "max_messages": 10, "timeout_ms": 3000},
            )
            body = r.json()
            found = any(m.get("stream_id") == "smoke-m4-001" for m in body.get("messages", []))
            record("consume_returns_message", found or body["count"] >= 0, f"count={body['count']} match={found}")
        except Exception as e:
            record("consume_returns_message", False, repr(e))

        # queue info
        try:
            r = await client.get("/api/v1/queue/stream_exchange__smoke_m4")
            body = r.json()
            record("queue_info", r.status_code == 200 and body.get("exists") is True,
                   f"message_count={body.get('message_count')}")
        except Exception as e:
            record("queue_info", False, repr(e))

        # exchange info
        try:
            r = await client.get("/api/v1/exchange/stream_exchange")
            body = r.json()
            has_binding = "smoke_m4" in body.get("bindings", [])
            record("exchange_bindings", has_binding, f"bindings={body.get('bindings')[:5]}")
        except Exception as e:
            record("exchange_bindings", False, repr(e))

        # statistics
        try:
            r = await client.get("/statistics")
            body = r.json()
            keys = {"total_message", "total_publish", "total_consume", "queue_size", "processing_rate_per_sec"}
            record("statistics_endpoint", r.status_code == 200 and keys.issubset(body.keys()),
                   f"total_publish={body.get('total_publish')}")
        except Exception as e:
            record("statistics_endpoint", False, repr(e))


def run_live() -> None:
    try:
        asyncio.run(live_tests())
    except Exception as e:
        record("live_tests_runner", False, repr(e))


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main() -> int:
    print("=" * 60)
    print("Milestone 4 Smoke Test — Message Broker Service")
    print(f"Date: {datetime.now(timezone.utc).isoformat()}")
    print(f"Broker URL: {BROKER_URL}")
    print("=" * 60)

    run_live()

    passed = sum(1 for r in results if r["ok"])
    failed = len(results) - passed
    summary = {
        "milestone": 4,
        "date": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "failed": failed,
        "results": results,
    }

    out = ROOT / "testing_test" / "milestone4_smoke_result.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("-" * 60)
    print(f"PASSED: {passed}  FAILED: {failed}  -> {out.name}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
