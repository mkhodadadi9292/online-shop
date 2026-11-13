"""Unit tests for order use cases."""

from __future__ import annotations

import pytest

from shop_shared.errors import NotFoundError, ValidationError

from order_service.application.order_service import OrderService
from order_service.application.ports import ProductInfo
from order_service.domain.order import OrderStatus
from tests.unit.fakes import FakeCatalogClient, FakeOrderRepository, RecordingPublisher


@pytest.fixture
def service():
    repo = FakeOrderRepository()
    publisher = RecordingPublisher()
    catalog = FakeCatalogClient(
        {"p1": ProductInfo("p1", "Widget", 1000), "p2": ProductInfo("p2", "Gadget", 500)}
    )
    return OrderService(repo, publisher, catalog), publisher


async def test_create_order_fetches_prices_and_publishes(service):
    svc, publisher = service
    order = await svc.create_order("u1", [{"product_id": "p1", "quantity": 2}])
    assert order.total_amount == 2000
    assert order.status == OrderStatus.RESERVING
    assert len(publisher.events) == 1
    assert publisher.events[0].type == "order.created"


async def test_create_order_unknown_product_raises(service):
    svc, _ = service
    with pytest.raises(NotFoundError):
        await svc.create_order("u1", [{"product_id": "missing", "quantity": 1}])


async def test_create_order_empty_items_raises(service):
    svc, _ = service
    with pytest.raises(ValidationError):
        await svc.create_order("u1", [])


async def test_get_missing_raises(service):
    svc, _ = service
    with pytest.raises(NotFoundError):
        await svc.get_order("missing")
