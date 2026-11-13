"""SQLAlchemy implementation of the PaymentRepository port."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payment_service.domain.payment import Payment, PaymentStatus
from payment_service.infrastructure.models import PaymentModel


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, payment_id: str) -> Payment | None:
        model = await self._session.get(PaymentModel, payment_id)
        return self._to_domain(model) if model else None

    async def get_by_order(self, order_id: str) -> Payment | None:
        result = await self._session.execute(
            select(PaymentModel).where(PaymentModel.order_id == order_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def add(self, payment: Payment) -> None:
        self._session.add(self._to_model(payment))
        await self._session.flush()

    async def update(self, payment: Payment) -> None:
        model = await self._session.get(PaymentModel, payment.id)
        if model is None:
            return
        model.status = payment.status.value
        model.reference = payment.reference
        await self._session.flush()

    @staticmethod
    def _to_domain(model: PaymentModel) -> Payment:
        return Payment(
            id=model.id,
            order_id=model.order_id,
            amount=model.amount,
            status=PaymentStatus(model.status),
            reference=model.reference,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(payment: Payment) -> PaymentModel:
        return PaymentModel(
            id=payment.id,
            order_id=payment.order_id,
            amount=payment.amount,
            status=payment.status.value,
            reference=payment.reference,
        )
