"""Integration tests for the order repository (JSON items round-trip)."""

from __future__ import annotations

from order_service.domain.order import Order, OrderItem, OrderStatus
from order_service.infrastructure.repositories import SqlAlchemyOrderRepository


async def test_add_and_fetch(session):
    repo = SqlAlchemyOrderRepository(session)
    order = Order.create("u1", [OrderItem("p1", 2, 500), OrderItem("p2", 1, 1500)])
    await repo.add(order)
    await session.commit()

    fetched = await repo.get(order.id)
    assert fetched is not None
    assert fetched.total_amount == 2500
    assert fetched.items[0].product_id == "p1"
    assert fetched.items[1].quantity == 1


async def test_update_status(session):
    repo = SqlAlchemyOrderRepository(session)
    order = Order.create("u1", [OrderItem("p1", 1, 100)])
    await repo.add(order)
    await session.commit()

    order.confirm()
    await repo.update(order)
    await session.commit()

    fetched = await repo.get(order.id)
    assert fetched.status == OrderStatus.CONFIRMED


async def test_list_by_user(session):
    repo = SqlAlchemyOrderRepository(session)
    await repo.add(Order.create("u1", [OrderItem("p1", 1, 100)]))
    await repo.add(Order.create("u2", [OrderItem("p1", 1, 100)]))
    await session.commit()
    assert len(await repo.list_by_user("u1")) == 1
    assert len(await repo.list_by_user("u2")) == 1
