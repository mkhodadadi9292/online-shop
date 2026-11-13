"""Ports the application layer depends on."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from shop_shared.events import Event

from order_service.domain.order import Order


class OrderRepository(Protocol):
    async def get(self, order_id: str) -> Order | None: ...

    async def list_by_user(self, user_id: str) -> list[Order]: ...

    async def add(self, order: Order) -> None: ...

    async def update(self, order: Order) -> None: ...

    async def commit(self) -> None: ...


class EventPublisher(Protocol):
    async def publish(self, event: Event) -> None: ...


@dataclass(frozen=True)
class ProductInfo:
    product_id: str
    name: str
    price: int


class CatalogClient(Protocol):
    async def get_product(self, product_id: str) -> ProductInfo | None: ...
