"""Ports the application layer depends on."""

from __future__ import annotations

from typing import Protocol

from payment_service.domain.payment import Payment


class PaymentRepository(Protocol):
    async def get(self, payment_id: str) -> Payment | None: ...

    async def get_by_order(self, order_id: str) -> Payment | None: ...

    async def add(self, payment: Payment) -> None: ...

    async def update(self, payment: Payment) -> None: ...


class PaymentGateway(Protocol):
    async def charge(self, order_id: str, amount: int) -> str:
        """Charge the customer; returns a provider reference.

        Raises PaymentError on failure.
        """
        ...
