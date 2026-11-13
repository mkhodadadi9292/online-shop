"""SQLAlchemy implementation of the InventoryRepository port.

The reserve/release operations use atomic conditional UPDATE ... RETURNING so
concurrent requests are serialized by the database row lock and cannot oversell
(see docs/06-race-conditions-and-locking.md).
"""

from __future__ import annotations

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from inventory_service.domain.inventory import (
    InsufficientStockError,
    InventoryItem,
    InvalidQuantityError,
)
from inventory_service.infrastructure.models import InventoryModel


class SqlAlchemyInventoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, product_id: str) -> InventoryItem | None:
        model = await self._session.get(InventoryModel, product_id)
        return self._to_domain(model) if model else None

    async def create(self, product_id: str, stock: int) -> InventoryItem:
        if stock < 0:
            raise InvalidQuantityError("stock cannot be negative")
        model = InventoryModel(product_id=product_id, stock=stock, reserved=0)
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def reserve(self, product_id: str, quantity: int) -> InventoryItem:
        if quantity <= 0:
            raise InvalidQuantityError("quantity must be positive")

        stmt = (
            update(InventoryModel)
            .where(
                InventoryModel.product_id == product_id,
                InventoryModel.stock >= quantity,
            )
            .values(
                stock=InventoryModel.stock - quantity,
                reserved=InventoryModel.reserved + quantity,
            )
            .returning(InventoryModel.stock, InventoryModel.reserved)
        )
        row = (await self._session.execute(stmt)).first()
        if row is None:
            available = await self._available(product_id)
            raise InsufficientStockError(product_id, quantity, available)
        return InventoryItem(product_id=product_id, stock=row.stock, reserved=row.reserved)

    async def release(self, product_id: str, quantity: int) -> InventoryItem:
        if quantity <= 0:
            raise InvalidQuantityError("quantity must be positive")

        stmt = (
            update(InventoryModel)
            .where(
                InventoryModel.product_id == product_id,
                InventoryModel.reserved >= quantity,
            )
            .values(
                stock=InventoryModel.stock + quantity,
                reserved=InventoryModel.reserved - quantity,
            )
            .returning(InventoryModel.stock, InventoryModel.reserved)
        )
        row = (await self._session.execute(stmt)).first()
        if row is None:
            raise InsufficientStockError(product_id, quantity, 0)
        return InventoryItem(product_id=product_id, stock=row.stock, reserved=row.reserved)

    async def adjust_stock(self, product_id: str, delta: int) -> InventoryItem:
        stmt = (
            update(InventoryModel)
            .where(
                InventoryModel.product_id == product_id,
                InventoryModel.stock + delta >= 0,
            )
            .values(stock=InventoryModel.stock + delta)
            .returning(InventoryModel.stock, InventoryModel.reserved)
        )
        row = (await self._session.execute(stmt)).first()
        if row is None:
            raise InsufficientStockError(product_id, -delta, await self._available(product_id))
        return InventoryItem(product_id=product_id, stock=row.stock, reserved=row.reserved)

    async def _available(self, product_id: str) -> int:
        item = await self.get(product_id)
        return item.stock if item else 0

    @staticmethod
    def _to_domain(model: InventoryModel) -> InventoryItem:
        return InventoryItem(
            product_id=model.product_id,
            stock=model.stock,
            reserved=model.reserved,
        )
