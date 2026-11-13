"""Ports the application layer depends on."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from inventory_service.domain.inventory import InventoryItem


class InventoryRepository(Protocol):
    async def get(self, product_id: str) -> InventoryItem | None: ...

    async def create(self, product_id: str, stock: int) -> InventoryItem: ...

    async def reserve(self, product_id: str, quantity: int) -> InventoryItem:
        """Atomically decrement stock / increment reserved.

        Raises InsufficientStockError if stock < quantity.
        """

    async def release(self, product_id: str, quantity: int) -> InventoryItem:
        """Atomically increment stock / decrement reserved."""

    async def adjust_stock(self, product_id: str, delta: int) -> InventoryItem: ...


class DistributedLock(Protocol):
    def acquire(self, key: str) -> AbstractAsyncContextManager[bool]:
        """Acquire a named lock; the context yields True if acquired."""
        ...


class IdempotencyStore(Protocol):
    async def is_processed(self, key: str) -> bool: ...

    async def mark_processed(self, key: str) -> None: ...
