"""Run the Streaming Preprocessing Service."""

from __future__ import annotations

import uvicorn

from app.core.config import settings
from app.core import app


if __name__ == "__main__":
    uvicorn.run(app, host=settings.SERVICE_HOST, port=settings.SERVICE_PORT, reload=True)
