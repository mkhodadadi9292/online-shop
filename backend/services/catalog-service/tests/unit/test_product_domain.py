"""Unit tests for the product domain."""

from __future__ import annotations

import pytest

from catalog_service.domain.product import InvalidPriceError, Product


def test_create_product_defaults():
    product = Product.create("Widget", "A thing", 1000, "tools")
    assert product.id
    assert product.price == 1000
    assert product.image_url is None


def test_create_product_rejects_negative_price():
    with pytest.raises(InvalidPriceError):
        Product.create("Widget", "A thing", -1, "tools")


def test_change_price_updates_and_validates():
    product = Product.create("Widget", "A thing", 1000, "tools")
    product.change_price(2000)
    assert product.price == 2000
    with pytest.raises(InvalidPriceError):
        product.change_price(-5)
