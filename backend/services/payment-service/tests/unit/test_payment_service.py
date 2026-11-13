"""Unit tests for payment use cases."""

from __future__ import annotations

import pytest

from shop_shared.errors import ConflictError, NotFoundError

from payment_service.application.payment_service import PaymentService
from payment_service.domain.payment import PaymentStatus
from tests.unit.fakes import FakePaymentRepository, FailingGateway, SuccessGateway


async def test_process_completes_on_success():
    service = PaymentService(FakePaymentRepository(), SuccessGateway())
    payment = await service.process("order-1", 1000)
    assert payment.status == PaymentStatus.COMPLETED
    assert payment.reference == "ref-123"


async def test_process_marks_failed_on_decline():
    service = PaymentService(FakePaymentRepository(), FailingGateway())
    payment = await service.process("order-1", 1000)
    assert payment.status == PaymentStatus.FAILED


async def test_process_is_idempotent_by_order():
    repo = FakePaymentRepository()
    service = PaymentService(repo, SuccessGateway())
    first = await service.process("order-1", 1000)
    second = await service.process("order-1", 1000)
    assert first.id == second.id


async def test_refund_completed_payment():
    service = PaymentService(FakePaymentRepository(), SuccessGateway())
    payment = await service.process("order-1", 1000)
    refunded = await service.refund(payment.id)
    assert refunded.status == PaymentStatus.REFUNDED


async def test_refund_failed_payment_raises():
    service = PaymentService(FakePaymentRepository(), FailingGateway())
    payment = await service.process("order-1", 1000)
    with pytest.raises(ConflictError):
        await service.refund(payment.id)


async def test_get_missing_raises():
    service = PaymentService(FakePaymentRepository(), SuccessGateway())
    with pytest.raises(NotFoundError):
        await service.get("missing")
