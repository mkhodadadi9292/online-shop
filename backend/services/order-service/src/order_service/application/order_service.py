"""Order use cases."""

from __future__ import annotations

from shop_shared.errors import NotFoundError, ValidationError
from shop_shared.events import OrderCreated

from order_service.application.ports import (
    CatalogClient,
    EventPublisher,
    OrderRepository,
)
from order_service.domain.order import Order, OrderItem


class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        publisher: EventPublisher,
        catalog: CatalogClient,
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        self._catalog = catalog

    async def create_order(
        self,
        user_id: str,
        items: list[dict],
    ) -> Order:
        if not items:
            raise ValidationError("Order must contain at least one item")

        order_items: list[OrderItem] = []
        for raw in items:
            product_id = raw["product_id"]
            quantity = raw["quantity"]
            if quantity <= 0:
                raise ValidationError("quantity must be positive")
            product = await self._catalog.get_product(product_id)
            if product is None:
                raise NotFoundError(f"Product {product_id} not found")
            order_items.append(
                OrderItem(
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=product.price,
                )
            )

        order = Order.create(user_id, order_items)
        order.mark_reserving()
        await self._repository.add(order)
        # Commit before publishing so the orchestrator (this service's own
        # consumer) can always read the order when the saga reply arrives.
        await self._repository.commit()

        await self._publisher.publish(
            OrderCreated(
                correlation_id=order.id,
                order_id=order.id,
                user_id=user_id,
                items=[
                    {"product_id": i.product_id, "quantity": i.quantity, "unit_price": i.unit_price}
                    for i in order_items
                ],
                total_amount=order.total_amount,
            )
        )
        return order

    async def get_order(self, order_id: str) -> Order:
        order = await self._repository.get(order_id)
        if order is None:
            raise NotFoundError("Order not found")
        return order

    async def list_orders(self, user_id: str) -> list[Order]:
        return await self._repository.list_by_user(user_id)
