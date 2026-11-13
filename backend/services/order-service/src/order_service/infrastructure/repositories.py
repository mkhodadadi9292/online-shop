"""SQLAlchemy implementation of the OrderRepository port."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from order_service.domain.order import Order, OrderItem, OrderStatus
from order_service.infrastructure.models import OrderModel


class SqlAlchemyOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, order_id: str) -> Order | None:
        model = await self._session.get(OrderModel, order_id)
        return self._to_domain(model) if model else None

    async def list_by_user(self, user_id: str) -> list[Order]:
        result = await self._session.execute(
            select(OrderModel)
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.created_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def add(self, order: Order) -> None:
        self._session.add(self._to_model(order))
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def update(self, order: Order) -> None:
        model = await self._session.get(OrderModel, order.id)
        if model is None:
            return
        model.status = order.status.value
        model.total_amount = order.total_amount
        model.items = [self._item_to_dict(i) for i in order.items]
        await self._session.flush()

    @staticmethod
    def _item_to_dict(item: OrderItem) -> dict:
        return {
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
        }

    @staticmethod
    def _to_domain(model: OrderModel) -> Order:
        return Order(
            id=model.id,
            user_id=model.user_id,
            items=[OrderItem(**i) for i in model.items],
            total_amount=model.total_amount,
            status=OrderStatus(model.status),
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(order: Order) -> OrderModel:
        return OrderModel(
            id=order.id,
            user_id=order.user_id,
            items=[SqlAlchemyOrderRepository._item_to_dict(i) for i in order.items],
            total_amount=order.total_amount,
            status=order.status.value,
        )
