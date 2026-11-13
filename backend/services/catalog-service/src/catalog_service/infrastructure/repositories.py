"""SQLAlchemy implementation of the ProductRepository port."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from catalog_service.application.ports import ProductFilter
from catalog_service.domain.product import Product
from catalog_service.infrastructure.models import ProductModel


class SqlAlchemyProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, product_id: str) -> Product | None:
        model = await self._session.get(ProductModel, product_id)
        return self._to_domain(model) if model else None

    async def add(self, product: Product) -> None:
        self._session.add(self._to_model(product))
        await self._session.flush()

    async def update(self, product: Product) -> None:
        model = await self._session.get(ProductModel, product.id)
        if model is None:
            return
        model.name = product.name
        model.description = product.description
        model.price = product.price
        model.category = product.category
        model.image_url = product.image_url
        await self._session.flush()

    async def delete(self, product_id: str) -> bool:
        model = await self._session.get(ProductModel, product_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def list(self, filters: ProductFilter) -> tuple[list[Product], int]:
        conditions = []
        if filters.search:
            pattern = f"%{filters.search}%"
            conditions.append(
                or_(
                    ProductModel.name.ilike(pattern),
                    ProductModel.description.ilike(pattern),
                )
            )
        if filters.category:
            conditions.append(ProductModel.category == filters.category)
        if filters.min_price is not None:
            conditions.append(ProductModel.price >= filters.min_price)
        if filters.max_price is not None:
            conditions.append(ProductModel.price <= filters.max_price)

        base = select(ProductModel)
        if conditions:
            base = base.where(*conditions)

        total = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()

        ordering = {
            "price_asc": ProductModel.price.asc(),
            "price_desc": ProductModel.price.desc(),
            "newest": ProductModel.created_at.desc(),
        }
        order_by = ordering.get(filters.sort, ProductModel.created_at.desc())

        result = await self._session.execute(
            base.order_by(order_by).offset(filters.offset).limit(filters.page_size)
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models], total

    @staticmethod
    def _to_domain(model: ProductModel) -> Product:
        return Product(
            id=model.id,
            name=model.name,
            description=model.description,
            price=model.price,
            category=model.category,
            image_url=model.image_url,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(product: Product) -> ProductModel:
        return ProductModel(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            category=product.category,
            image_url=product.image_url,
        )
