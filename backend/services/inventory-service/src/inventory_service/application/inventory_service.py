"""Inventory use cases.

The reserve/release critical section is guarded by a DistributedLock; the actual
correctness comes from the repository's atomic conditional UPDATE (see
docs/06-race-conditions-and-locking.md). The lock serializes cross-service access
to the same product; the SQL guard remains the source of truth under concurrency.
"""

from __future__ import annotations

from shop_shared.errors import ConflictError, NotFoundError

from inventory_service.application.ports import (
    DistributedLock,
    InventoryRepository,
)
from inventory_service.domain.inventory import (
    InsufficientStockError,
    InventoryItem,
)


class InventoryService:
    def __init__(
        self,
        repository: InventoryRepository,
        lock: DistributedLock | None = None,
    ) -> None:
        self._repository = repository
        self._lock = lock

    async def get(self, product_id: str) -> InventoryItem:
        item = await self._repository.get(product_id)
        if item is None:
            raise NotFoundError("Inventory not found")
        return item

    async def create(self, product_id: str, stock: int) -> InventoryItem:
        return await self._repository.create(product_id, stock)

    async def reserve(self, product_id: str, quantity: int) -> InventoryItem:
        if self._lock is None:
            return await self._repository.reserve(product_id, quantity)
        async with self._lock.acquire(f"lock:inventory:{product_id}") as acquired:
            if not acquired:
                raise ConflictError("Could not acquire inventory lock, retry")
            return await self._repository.reserve(product_id, quantity)

    async def release(self, product_id: str, quantity: int) -> InventoryItem:
        if self._lock is None:
            return await self._repository.release(product_id, quantity)
        async with self._lock.acquire(f"lock:inventory:{product_id}") as acquired:
            if not acquired:
                raise ConflictError("Could not acquire inventory lock, retry")
            return await self._repository.release(product_id, quantity)

    async def adjust_stock(self, product_id: str, delta: int) -> InventoryItem:
        return await self._repository.adjust_stock(product_id, delta)


__all__ = ["InventoryService", "InsufficientStockError"]
