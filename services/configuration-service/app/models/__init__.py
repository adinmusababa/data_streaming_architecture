"""Database models for the Configuration Service."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for configuration models."""


class ConfigurationModel(Base):
    """Stored configuration for one service."""

    __tablename__ = "configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    config_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "service_name": self.service_name,
            "config_data": self.config_data,
            "version": self.version,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
