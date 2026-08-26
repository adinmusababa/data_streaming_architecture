"""Application settings for Message Broker Service."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    SERVICE_NAME: str = "message-broker"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8003
    LOG_LEVEL: str = "INFO"
    CONFIG_SERVICE_URL: str = "http://localhost:8001"

    # Safe bootstrap defaults only; runtime values come from Configuration Service.
    DEFAULT_BROKER_CONFIG: dict[str, object] = Field(
        default_factory=lambda: {
            "host": "localhost",
            "port": 9092,
            "username": "",
            "password": "",
            "exchange": "stream_exchange",
            "queue": "stream_queue",
            "routing_key": "stream_data",
            "prefetch_count": 100,
            "retry_count": 3,
        }
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
