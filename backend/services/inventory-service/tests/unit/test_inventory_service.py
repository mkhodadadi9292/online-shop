"""Unit tests for inventory use cases with a fake repository."""

from __future__ import annotations

import pytest

from shop_shared.errors import NotFoundError

from inventory_service.application.inventory_service import InventoryService
from inventory_service.domain.inventory import InsufficientStockError
from inventory_service.infrastructure.locking import NoopLock
from tests.unit.fakes import FakeInventoryRepository


@pytest.fixture
def service():
    return InventoryService(FakeInventoryRepository(), NoopLock())


async def test_reserve_decrements_stock(service):
    await service.create("p1", 10)
    item = await service.reserve("p1", 3)
    assert item.stock == 7
    assert item.reserved == 3


async def test_reserve_insufficient_raises(service):
    await service.create("p1", 2)
    with pytest.raises(InsufficientStockError):
        await service.reserve("p1", 3)


async def test_release_restores_stock(service):
    await service.create("p1", 10)
    await service.reserve("p1", 4)
    item = await service.release("p1", 4)
    assert item.stock == 10
    assert item.reserved == 0


async def test_get_missing_raises(service):
    with pytest.raises(NotFoundError):
        await service.get("missing")


async def test_adjust_stock(service):
    await service.create("p1", 5)
    item = await service.adjust_stock("p1", 5)
    assert item.stock == 10
