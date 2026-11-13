"""Integration tests for the inventory repository, including the critical
race-condition test: concurrent reservations must never oversell limited stock.
"""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from inventory_service.domain.inventory import InsufficientStockError
from inventory_service.infrastructure.repositories import SqlAlchemyInventoryRepository


async def test_create_and_reserve(session):
    repo = SqlAlchemyInventoryRepository(session)
    await repo.create("p1", 10)
    await session.commit()

    item = await repo.reserve("p1", 3)
    await session.commit()
    assert item.stock == 7
    assert item.reserved == 3


async def test_reserve_insufficient_raises(session):
    repo = SqlAlchemyInventoryRepository(session)
    await repo.create("p1", 1)
    await session.commit()
    with pytest.raises(InsufficientStockError):
        await repo.reserve("p1", 2)


async def test_release_restores(session):
    repo = SqlAlchemyInventoryRepository(session)
    await repo.create("p1", 5)
    await session.commit()
    await repo.reserve("p1", 5)
    await session.commit()
    item = await repo.release("p1", 5)
    await session.commit()
    assert item.stock == 5
    assert item.reserved == 0


async def test_concurrent_reserve_does_not_oversell(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        await SqlAlchemyInventoryRepository(session).create("hot-product", 10)
        await session.commit()

    async def attempt() -> bool:
        async with factory() as session:
            repo = SqlAlchemyInventoryRepository(session)
            try:
                await repo.reserve("hot-product", 1)
                await session.commit()
                return True
            except InsufficientStockError:
                await session.rollback()
                return False

    results = await asyncio.gather(*[attempt() for _ in range(30)])

    assert results.count(True) == 10
    assert results.count(False) == 20

    async with factory() as session:
        repo = SqlAlchemyInventoryRepository(session)
        item = await repo.get("hot-product")
        assert item.stock == 0
        assert item.reserved == 10
