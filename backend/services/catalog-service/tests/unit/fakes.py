"""In-memory fake ProductRepository (unit tests only)."""

from __future__ import annotations

from catalog_service.application.ports import ProductFilter
from catalog_service.domain.product import Product


class FakeProductRepository:
    def __init__(self) -> None:
        self._items: dict[str, Product] = {}

    async def get_by_id(self, product_id: str) -> Product | None:
        return self._items.get(product_id)

    async def add(self, product: Product) -> None:
        self._items[product.id] = product

    async def update(self, product: Product) -> None:
        self._items[product.id] = product

    async def delete(self, product_id: str) -> bool:
        return self._items.pop(product_id, None) is not None

    async def list(self, filters: ProductFilter) -> tuple[list[Product], int]:
        items = list(self._items.values())
        if filters.category:
            items = [p for p in items if p.category == filters.category]
        if filters.min_price is not None:
            items = [p for p in items if p.price >= filters.min_price]
        if filters.max_price is not None:
            items = [p for p in items if p.price <= filters.max_price]
        if filters.search:
            needle = filters.search.lower()
            items = [
                p for p in items
                if needle in p.name.lower() or needle in p.description.lower()
            ]
        total = len(items)
        return items[filters.offset : filters.offset + filters.page_size], total
