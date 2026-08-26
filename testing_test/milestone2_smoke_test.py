from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Musa\OneDrive - Universitas Teknologi Yogyakarta (1)\integrasi data streaming infastuktur\streaming-platform\services\configuration-service")
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

results = []


def record(name: str, ok: bool, detail: str) -> None:
    results.append({"name": name, "ok": ok, "detail": detail})


# Import checks
try:
    import fastapi  # noqa: F401
    record("import_fastapi", True, "fastapi import ok")
except Exception as e:
    record("import_fastapi", False, repr(e))

try:
    import sqlalchemy  # noqa: F401
    record("import_sqlalchemy", True, "sqlalchemy import ok")
except Exception as e:
    record("import_sqlalchemy", False, repr(e))

# App import
app = None
try:
    from app.core import app as fastapi_app
    app = fastapi_app
    record("import_app", True, f"app title={fastapi_app.title}")
except Exception as e:
    record("import_app", False, repr(e))

# Endpoint smoke tests
if app is not None:
    try:
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            checks = [
                ("GET /api/v1/health", "get", "/api/v1/health", None),
                ("GET /api/v1/status", "get", "/api/v1/status", None),
                ("GET /api/v1/config", "get", "/api/v1/config", None),
                (
                    "PUT /api/v1/config",
                    "put",
                    "/api/v1/config",
                    {
                        "service_name": "test-service",
                        "config_data": {"enabled": True, "timeout": 10},
                        "description": "Smoke test configuration",
                    },
                ),
                ("POST /api/v1/config/reload", "post", "/api/v1/config/reload", {"force": True}),
            ]

            for label, method, path, payload in checks:
                try:
                    if method == "get":
                        response = client.get(path)
                    elif method == "put":
                        response = client.put(path, json=payload)
                    else:
                        response = client.post(path, json=payload)

                    body = response.json()
                    record(
                        label,
                        response.status_code < 400,
                        json.dumps({"status_code": response.status_code, "body": body}, default=str),
                    )
                except Exception as e:
                    record(label, False, repr(e))
    except Exception as e:
        record("endpoint_smoke_setup", False, repr(e))

# Print results for downstream report creation
for item in results:
    status = "PASS" if item["ok"] else "FAIL"
    print(f"{item['name']}\t{status}\t{item['detail']}")

failed = [item for item in results if not item["ok"]]
print(f"TOTAL\t{len(results)}")
print(f"FAILED\t{len(failed)}")
