"""Unit tests for catalog use cases with a fake repository."""

from __future__ import annotations

import pytest

from shop_shared.errors import NotFoundError

from catalog_service.application.catalog_service import CatalogService
from catalog_service.application.ports import ProductFilter
from tests.unit.fakes import FakeProductRepository


@pytest.fixture
def service():
    return CatalogService(FakeProductRepository())


async def test_create_and_get(service):
    product = await service.create_product("Widget", "desc", 1000, "tools")
    found = await service.get_product(product.id)
    assert found.name == "Widget"


async def test_get_missing_raises(service):
    with pytest.raises(NotFoundError):
        await service.get_product("missing")


async def test_update_price(service):
    product = await service.create_product("Widget", "desc", 1000, "tools")
    updated = await service.update_product(product.id, price=2500)
    assert updated.price == 2500


async def test_delete(service):
    product = await service.create_product("Widget", "desc", 1000, "tools")
    await service.delete_product(product.id)
    with pytest.raises(NotFoundError):
        await service.get_product(product.id)


async def test_list_filters_by_category(service):
    await service.create_product("Hammer", "tool", 1000, "tools")
    await service.create_product("Shirt", "clothes", 500, "apparel")
    page = await service.list_products(ProductFilter(category="tools"))
    assert page.total == 1
    assert page.items[0].name == "Hammer"
