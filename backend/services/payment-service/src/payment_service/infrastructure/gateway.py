"""Mock payment gateway.

Real integration would call a PSP (Stripe, Adyen, ...). For this learning project
we simulate success, with an optional amount that always declines so tests can
exercise the saga's compensation path.
"""

from __future__ import annotations

from uuid import uuid4

from shop_shared.errors import PaymentError


class MockPaymentGateway:
    def __init__(self, decline_amount: int | None = None) -> None:
        self._decline_amount = decline_amount

    async def charge(self, order_id: str, amount: int) -> str:
        if self._decline_amount is not None and amount == self._decline_amount:
            raise PaymentError("Card declined by mock gateway")
        return f"mock-{uuid4().hex[:12]}"
