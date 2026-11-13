"""Payment use cases."""

from __future__ import annotations

from shop_shared.errors import ConflictError, NotFoundError, PaymentError

from payment_service.application.ports import PaymentGateway, PaymentRepository
from payment_service.domain.payment import Payment, PaymentStatus


class PaymentService:
    def __init__(self, repository: PaymentRepository, gateway: PaymentGateway) -> None:
        self._repository = repository
        self._gateway = gateway

    async def process(self, order_id: str, amount: int) -> Payment:
        existing = await self._repository.get_by_order(order_id)
        if existing is not None and existing.status == PaymentStatus.COMPLETED:
            return existing

        payment = Payment.create(order_id, amount)
        await self._repository.add(payment)

        try:
            reference = await self._gateway.charge(order_id, amount)
        except PaymentError:
            payment.fail()
            await self._repository.update(payment)
            return payment

        payment.complete(reference)
        await self._repository.update(payment)
        return payment

    async def get(self, payment_id: str) -> Payment:
        payment = await self._repository.get(payment_id)
        if payment is None:
            raise NotFoundError("Payment not found")
        return payment

    async def refund(self, payment_id: str) -> Payment:
        payment = await self.get(payment_id)
        if payment.status != PaymentStatus.COMPLETED:
            raise ConflictError("Only completed payments can be refunded")
        payment.refund()
        await self._repository.update(payment)
        return payment
