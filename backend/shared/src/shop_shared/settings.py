"""Common configuration shared by every service.

Each service defines its own concrete settings subclass (e.g. UserServiceSettings)
that inherits from CommonSettings and adds service-specific values. Environment
variables override the defaults, which keeps 12-factor style configuration.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_prefix="")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "insecure-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Exchange/binding used by the saga message flow.
    events_exchange: str = "shop.events"
