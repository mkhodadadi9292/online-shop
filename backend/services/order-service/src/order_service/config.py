"""Order Service configuration."""

from __future__ import annotations

from shop_shared.settings import CommonSettings


class Settings(CommonSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/orders_db"
    catalog_service_url: str = "http://localhost:8001"


def get_settings() -> Settings:
    return Settings()
