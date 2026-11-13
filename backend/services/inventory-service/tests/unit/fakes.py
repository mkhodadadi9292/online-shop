"""In-memory fake InventoryRepository (unit tests only)."""

from __future__ import annotations

from inventory_service.domain.inventory import (
    InsufficientStockError,
    InventoryItem,
)


class FakeInventoryRepository:
    def __init__(self) -> None:
        self._items: dict[str, InventoryItem] = {}

    async def get(self, product_id: str) -> InventoryItem | None:
        return self._items.get(product_id)

    async def create(self, product_id: str, stock: int) -> InventoryItem:
        item = InventoryItem.new(product_id, stock)
        self._items[product_id] = item
        return item

    async def reserve(self, product_id: str, quantity: int) -> InventoryItem:
        item = self._items.get(product_id)
        if item is None or item.stock < quantity:
            raise InsufficientStockError(product_id, quantity, item.stock if item else 0)
        updated = InventoryItem(product_id, item.stock - quantity, item.reserved + quantity)
        self._items[product_id] = updated
        return updated

    async def release(self, product_id: str, quantity: int) -> InventoryItem:
        item = self._items.get(product_id)
        if item is None or item.reserved < quantity:
            raise InsufficientStockError(product_id, quantity, 0)
        updated = InventoryItem(product_id, item.stock + quantity, item.reserved - quantity)
        self._items[product_id] = updated
        return updated

    async def adjust_stock(self, product_id: str, delta: int) -> InventoryItem:
        item = self._items.get(product_id)
        if item is None or item.stock + delta < 0:
            raise InsufficientStockError(product_id, -delta, item.stock if item else 0)
        updated = InventoryItem(product_id, item.stock + delta, item.reserved)
        self._items[product_id] = updated
        return updated
