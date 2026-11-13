"""Inventory aggregate and domain errors (pure, stdlib only)."""

from __future__ import annotations

from dataclasses import dataclass


class InsufficientStockError(Exception):
    def __init__(self, product_id: str, requested: int, available: int) -> None:
        super().__init__(
            f"Insufficient stock for {product_id}: requested {requested}, available {available}"
        )
        self.product_id = product_id
        self.requested = requested
        self.available = available


class InvalidQuantityError(ValueError):
    pass


@dataclass(frozen=True)
class InventoryItem:
    product_id: str
    stock: int
    reserved: int

    @property
    def available(self) -> int:
        return self.stock

    @classmethod
    def new(cls, product_id: str, stock: int) -> "InventoryItem":
        if stock < 0:
            raise InvalidQuantityError("stock cannot be negative")
        return cls(product_id=product_id, stock=stock, reserved=0)

    def can_reserve(self, quantity: int) -> bool:
        return 0 < quantity <= self.stock
