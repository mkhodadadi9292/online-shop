"""In-memory fakes for payment ports (unit tests only)."""

from __future__ import annotations

from shop_shared.errors import PaymentError

from payment_service.domain.payment import Payment


class FakePaymentRepository:
    def __init__(self) -> None:
        self._items: dict[str, Payment] = {}
        self._by_order: dict[str, Payment] = {}

    async def get(self, payment_id: str) -> Payment | None:
        return self._items.get(payment_id)

    async def get_by_order(self, order_id: str) -> Payment | None:
        return self._by_order.get(order_id)

    async def add(self, payment: Payment) -> None:
        self._items[payment.id] = payment
        self._by_order[payment.order_id] = payment

    async def update(self, payment: Payment) -> None:
        self._items[payment.id] = payment
        self._by_order[payment.order_id] = payment


class SuccessGateway:
    async def charge(self, order_id: str, amount: int) -> str:
        return "ref-123"


class FailingGateway:
    async def charge(self, order_id: str, amount: int) -> str:
        raise PaymentError("declined")
