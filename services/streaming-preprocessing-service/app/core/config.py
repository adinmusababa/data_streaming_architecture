"""Application settings for Streaming Preprocessing Service."""

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

    SERVICE_NAME: str = "streaming-preprocessing-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8002
    LOG_LEVEL: str = "INFO"
    CONFIG_SERVICE_URL: str = "http://localhost:8001"

    # Safe bootstrap defaults only; runtime values should come from Configuration Service.
    DEFAULT_STREAMING_CONFIG: dict[str, object] = Field(
        default_factory=lambda: {
            "source_type": "csv",
            "batch_size": 100,
            "polling_interval": 1.0,
            "preprocessing_pipeline": ["validation", "transformation"],
            "publish_topic": "stream_data",
            "retry_count": 3,
            "validation": {"enabled": True},
            "transformation": {},
            "features": {},
        }
    )

    # Broker connection defaults (used when Message Broker is available)
    BROKER_URL: str = "http://localhost:8003"
    BROKER_EXCHANGE: str = "stream_exchange"
    BROKER_ROUTING_KEY: str = "stream_data"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
