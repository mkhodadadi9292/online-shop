"""Catalog use cases."""

from __future__ import annotations

from dataclasses import dataclass

from shop_shared.errors import NotFoundError

from catalog_service.application.ports import ProductFilter, ProductRepository
from catalog_service.domain.product import Product


@dataclass
class ProductPage:
    items: list[Product]
    total: int
    page: int
    page_size: int


class CatalogService:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def get_product(self, product_id: str) -> Product:
        product = await self._repository.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    async def list_products(self, filters: ProductFilter) -> ProductPage:
        items, total = await self._repository.list(filters)
        return ProductPage(
            items=items,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    async def create_product(
        self,
        name: str,
        description: str,
        price: int,
        category: str,
        image_url: str | None = None,
    ) -> Product:
        product = Product.create(
            name=name,
            description=description,
            price=price,
            category=category,
            image_url=image_url,
        )
        await self._repository.add(product)
        return product

    async def update_product(
        self,
        product_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        price: int | None = None,
        category: str | None = None,
        image_url: str | None = None,
    ) -> Product:
        product = await self.get_product(product_id)
        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if price is not None:
            product.change_price(price)
        if category is not None:
            product.category = category
        if image_url is not None:
            product.image_url = image_url
        await self._repository.update(product)
        return product

    async def delete_product(self, product_id: str) -> None:
        deleted = await self._repository.delete(product_id)
        if not deleted:
            raise NotFoundError("Product not found")
