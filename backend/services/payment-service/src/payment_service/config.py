"""Payment Service configuration."""

from __future__ import annotations

from shop_shared.settings import CommonSettings


class Settings(CommonSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/payments_db"
    # When set, any charge for exactly this amount is declined — used by e2e
    # tests to exercise the saga's compensation path.
    decline_amount: int | None = None


def get_settings() -> Settings:
    return Settings()
