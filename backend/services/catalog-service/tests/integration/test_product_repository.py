"""Integration tests for the SQLAlchemy product repository."""

from __future__ import annotations

from catalog_service.application.ports import ProductFilter
from catalog_service.domain.product import Product
from catalog_service.infrastructure.repositories import SqlAlchemyProductRepository


async def _add(session, name, price, category, description="desc"):
    repo = SqlAlchemyProductRepository(session)
    await repo.add(Product.create(name, description, price, category))
    await session.commit()
    return repo


async def test_add_and_fetch(session):
    repo = SqlAlchemyProductRepository(session)
    product = Product.create("Widget", "desc", 1000, "tools")
    await repo.add(product)
    await session.commit()
    fetched = await repo.get_by_id(product.id)
    assert fetched is not None
    assert fetched.name == "Widget"


async def test_list_search_and_pagination(session):
    repo = SqlAlchemyProductRepository(session)
    await repo.add(Product.create("Hammer", "a tool", 1000, "tools"))
    await repo.add(Product.create("Drill", "power tool", 5000, "tools"))
    await repo.add(Product.create("Shirt", "apparel", 500, "apparel"))
    await session.commit()

    items, total = await repo.list(ProductFilter(search="tool"))
    assert total == 2

    items, total = await repo.list(ProductFilter(category="tools", sort="price_asc"))
    assert total == 2
    assert items[0].name == "Hammer"


async def test_delete(session):
    repo = SqlAlchemyProductRepository(session)
    product = Product.create("Widget", "desc", 1000, "tools")
    await repo.add(product)
    await session.commit()
    assert await repo.delete(product.id) is True
    assert await repo.delete(product.id) is False
