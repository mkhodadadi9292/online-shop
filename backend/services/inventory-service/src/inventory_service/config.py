"""Inventory Service configuration."""

from __future__ import annotations

from shop_shared.settings import CommonSettings


class Settings(CommonSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/inventory_db"


def get_settings() -> Settings:
    return Settings()
