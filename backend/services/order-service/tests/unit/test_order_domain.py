"""Unit tests for the order domain."""

from __future__ import annotations

from order_service.domain.order import Order, OrderItem, OrderStatus


def test_create_computes_total():
    order = Order.create(
        "u1",
        [OrderItem("p1", 2, 500), OrderItem("p2", 1, 1500)],
    )
    assert order.total_amount == 2500
    assert order.status == OrderStatus.PENDING


def test_status_transitions():
    order = Order.create("u1", [OrderItem("p1", 1, 100)])
    order.mark_reserving()
    assert order.status == OrderStatus.RESERVING
    order.mark_paying()
    assert order.status == OrderStatus.PAYING
    order.confirm()
    assert order.status == OrderStatus.CONFIRMED
