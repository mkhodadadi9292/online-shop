"""Shared fixtures for integration and e2e tests (requires Postgres container)."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from inventory_service.infrastructure.db import Base
from inventory_service.infrastructure.models import (  # noqa: F401
    InventoryModel,
    ProcessedEventModel,
)

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/inventory_db_test"


@pytest.fixture
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, pool_size=20)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
