"""Application settings for the Configuration Service."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    SERVICE_NAME: str = "configuration-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8001
    LOG_LEVEL: str = "INFO"

    # SQLite by default so the service runs out of the box.
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./configuration.db")

    # Canonical platform defaults. Other services will read these instead of hardcoding values.
    DEFAULT_CONFIGS: dict[str, dict] = Field(
        default_factory=lambda: {
            "configuration-service": {
                "service_host": "0.0.0.0",
                "service_port": 8001,
                "log_level": "INFO",
            },
            "streaming-preprocessing-service": {
                "source_type": "csv",
                "batch_size": 100,
                "polling_interval": 1.0,
                "preprocessing_pipeline": ["validation", "cleaning", "transformation"],
                "publish_topic": "stream_data",
                "retry_count": 3,
            },
            "message-broker": {
                "host": "localhost",
                "port": 5672,
                "username": "guest",
                "password": "guest",
                "exchange": "stream_exchange",
                "queue": "stream_queue",
                "routing_key": "stream.data",
                "prefetch_count": 100,
            },
            "online-ml-engine": {
                "model_name": "river_hoeffding_tree",
                "learning_rate": 0.01,
                "batch_size": 1,
                "state_interval": 500,
                "evaluation_interval": 100,
            },
            "state-store": {
                "storage_provider": "sqlite",
                "auto_save": True,
                "save_interval": 300,
                "max_versions": 10,
            },
            "storage-layer": {
                "provider": "sqlite",
                "timeout": 30,
                "retry": 3,
                "max_connections": 20,
            },
            "monitoring-dashboard": {
                "refresh_interval": 5,
            },
        }
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
