"""Ports the application layer depends on."""

from __future__ import annotations

from typing import Protocol

from catalog_service.domain.product import Product


class ProductFilter:
    """Search/filter/sort/pagination parameters (plain value object)."""

    def __init__(
        self,
        search: str | None = None,
        category: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        sort: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> None:
        self.search = search
        self.category = category
        self.min_price = min_price
        self.max_price = max_price
        self.sort = sort
        self.page = max(page, 1)
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class ProductRepository(Protocol):
    async def get_by_id(self, product_id: str) -> Product | None: ...

    async def add(self, product: Product) -> None: ...

    async def update(self, product: Product) -> None: ...

    async def delete(self, product_id: str) -> bool: ...

    async def list(self, filters: ProductFilter) -> tuple[list[Product], int]: ...
