"""Order saga orchestrator.

The Order Service drives the distributed transaction as a state machine:

    PENDING -> RESERVING -> PAYING -> CONFIRMED
                    |            |
                    v            v
                CANCELLED    CANCELLED (+ inventory.released compensation)

Each handler is guarded by the order's current status, so duplicate or
out-of-order events are ignored (defense in depth on top of idempotent
consumption).
"""

from __future__ import annotations

from shop_shared.events import (
    InventoryReleased,
    InventoryReservationFailed,
    InventoryReserved,
    OrderCancelled,
    OrderConfirmed,
    PaymentCompleted,
    PaymentFailed,
    PaymentRequested,
)

from order_service.application.ports import EventPublisher, OrderRepository
from order_service.domain.order import OrderStatus


class OrderSaga:
    def __init__(
        self,
        repository: OrderRepository,
        publisher: EventPublisher,
    ) -> None:
        self._repository = repository
        self._publisher = publisher

    async def handle_inventory_reserved(self, event: InventoryReserved) -> None:
        order = await self._repository.get(event.order_id)
        if order is None or order.status != OrderStatus.RESERVING:
            return
        order.mark_paying()
        await self._repository.update(order)
        await self._repository.commit()
        await self._publisher.publish(
            PaymentRequested(
                correlation_id=event.correlation_id,
                order_id=order.id,
                amount=order.total_amount,
            )
        )

    async def handle_inventory_reservation_failed(
        self, event: InventoryReservationFailed
    ) -> None:
        order = await self._repository.get(event.order_id)
        if order is None or order.status != OrderStatus.RESERVING:
            return
        order.cancel()
        await self._repository.update(order)
        await self._repository.commit()
        await self._publisher.publish(
            OrderCancelled(
                correlation_id=event.correlation_id,
                order_id=order.id,
                reason=event.reason,
            )
        )

    async def handle_payment_completed(self, event: PaymentCompleted) -> None:
        order = await self._repository.get(event.order_id)
        if order is None or order.status != OrderStatus.PAYING:
            return
        order.confirm()
        await self._repository.update(order)
        await self._repository.commit()
        await self._publisher.publish(
            OrderConfirmed(
                correlation_id=event.correlation_id,
                order_id=order.id,
            )
        )

    async def handle_payment_failed(self, event: PaymentFailed) -> None:
        order = await self._repository.get(event.order_id)
        if order is None or order.status != OrderStatus.PAYING:
            return
        order.cancel()
        await self._repository.update(order)
        await self._repository.commit()
        # Compensate: give the reserved stock back.
        await self._publisher.publish(
            InventoryReleased(
                correlation_id=event.correlation_id,
                order_id=order.id,
                items=[
                    {"product_id": i.product_id, "quantity": i.quantity, "unit_price": i.unit_price}
                    for i in order.items
                ],
            )
        )
        await self._publisher.publish(
            OrderCancelled(
                correlation_id=event.correlation_id,
                order_id=order.id,
                reason=event.reason,
            )
        )
