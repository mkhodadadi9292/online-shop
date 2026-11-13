"""Integration tests for the payment repository."""

from __future__ import annotations

from payment_service.domain.payment import Payment, PaymentStatus
from payment_service.infrastructure.repositories import SqlAlchemyPaymentRepository


async def test_add_and_fetch(session):
    repo = SqlAlchemyPaymentRepository(session)
    payment = Payment.create("order-1", 1000)
    payment.complete("ref-1")
    await repo.add(payment)
    await session.commit()

    fetched = await repo.get(payment.id)
    assert fetched is not None
    assert fetched.status == PaymentStatus.COMPLETED
    assert fetched.reference == "ref-1"


async def test_get_by_order(session):
    repo = SqlAlchemyPaymentRepository(session)
    await repo.add(Payment.create("order-1", 1000))
    await session.commit()
    assert (await repo.get_by_order("order-1")) is not None
    assert (await repo.get_by_order("missing")) is None
