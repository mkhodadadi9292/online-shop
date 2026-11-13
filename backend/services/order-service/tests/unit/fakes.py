"""In-memory fakes for order ports (unit tests only)."""

from __future__ import annotations

from shop_shared.events import Event

from order_service.application.ports import ProductInfo
from order_service.domain.order import Order


class FakeOrderRepository:
    def __init__(self) -> None:
        self._items: dict[str, Order] = {}

    async def get(self, order_id: str) -> Order | None:
        return self._items.get(order_id)

    async def list_by_user(self, user_id: str) -> list[Order]:
        return [o for o in self._items.values() if o.user_id == user_id]

    async def add(self, order: Order) -> None:
        self._items[order.id] = order

    async def update(self, order: Order) -> None:
        self._items[order.id] = order

    async def commit(self) -> None:
        return None


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[Event] = []

    async def publish(self, event: Event) -> None:
        self.events.append(event)


class FakeCatalogClient:
    def __init__(self, products: dict[str, ProductInfo] | None = None) -> None:
        self._products = products or {}

    async def get_product(self, product_id: str) -> ProductInfo | None:
        return self._products.get(product_id)
