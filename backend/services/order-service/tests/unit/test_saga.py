"""Unit tests for the saga orchestrator state machine."""

from __future__ import annotations

import pytest

from shop_shared.events import (
    InventoryReservationFailed,
    InventoryReserved,
    PaymentCompleted,
    PaymentFailed,
)

from order_service.application.saga import OrderSaga
from order_service.domain.order import Order, OrderItem, OrderStatus
from tests.unit.fakes import FakeOrderRepository, RecordingPublisher


@pytest.fixture
def saga():
    repo = FakeOrderRepository()
    publisher = RecordingPublisher()
    return OrderSaga(repo, publisher), repo, publisher


async def _seed(repo, status):
    order = Order.create("u1", [OrderItem("p1", 1, 1000)])
    order.status = status
    await repo.add(order)
    return order


async def test_inventory_reserved_moves_to_paying(saga):
    saga_svc, repo, publisher = saga
    order = await _seed(repo, OrderStatus.RESERVING)
    await saga_svc.handle_inventory_reserved(
        InventoryReserved(correlation_id=order.id, order_id=order.id, items=[])
    )
    assert (await repo.get(order.id)).status == OrderStatus.PAYING
    assert publisher.events[-1].type == "payment.requested"


async def test_inventory_reservation_failed_cancels(saga):
    saga_svc, repo, publisher = saga
    order = await _seed(repo, OrderStatus.RESERVING)
    await saga_svc.handle_inventory_reservation_failed(
        InventoryReservationFailed(correlation_id=order.id, order_id=order.id, reason="no stock")
    )
    assert (await repo.get(order.id)).status == OrderStatus.CANCELLED
    assert publisher.events[-1].type == "order.cancelled"


async def test_payment_failed_releases_and_cancels(saga):
    saga_svc, repo, publisher = saga
    order = await _seed(repo, OrderStatus.PAYING)
    await saga_svc.handle_payment_failed(
        PaymentFailed(correlation_id=order.id, order_id=order.id, reason="declined")
    )
    assert (await repo.get(order.id)).status == OrderStatus.CANCELLED
    types = [e.type for e in publisher.events]
    assert "inventory.released" in types
    assert "order.cancelled" in types


async def test_payment_completed_confirms(saga):
    saga_svc, repo, _ = saga
    order = await _seed(repo, OrderStatus.PAYING)
    await saga_svc.handle_payment_completed(
        PaymentCompleted(correlation_id=order.id, order_id=order.id, payment_id="pay-1")
    )
    assert (await repo.get(order.id)).status == OrderStatus.CONFIRMED


async def test_duplicate_event_is_ignored(saga):
    saga_svc, repo, publisher = saga
    order = await _seed(repo, OrderStatus.RESERVING)
    event = InventoryReserved(correlation_id=order.id, order_id=order.id, items=[])
    await saga_svc.handle_inventory_reserved(event)
    count = len(publisher.events)
    # Second delivery with the order already PAYING should be a no-op.
    await saga_svc.handle_inventory_reserved(event)
    assert len(publisher.events) == count
