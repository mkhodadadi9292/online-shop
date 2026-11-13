"""Unit tests for the inventory domain."""

from __future__ import annotations

import pytest

from inventory_service.domain.inventory import (
    InvalidQuantityError,
    InventoryItem,
)


def test_new_rejects_negative_stock():
    with pytest.raises(InvalidQuantityError):
        InventoryItem.new("p1", -1)


def test_can_reserve_logic():
    item = InventoryItem.new("p1", 5)
    assert item.can_reserve(5) is True
    assert item.can_reserve(6) is False
    assert item.can_reserve(0) is False
