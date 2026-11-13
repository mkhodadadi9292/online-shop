"""RabbitMQ consumer for the inventory saga participants.

Listens for order.created (reserve) and inventory.released (release), applies
idempotency on event_id, and publishes the reply events back onto the topic
exchange.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import aio_pika

from shop_shared.events import (
    InventoryReleased,
    InventoryReservationFailed,
    InventoryReserved,
    OrderCreated,
    deserialize_event,
)
from sqlalchemy.ext.asyncio import async_sessionmaker

from inventory_service.application.inventory_service import InventoryService
from inventory_service.domain.inventory import InsufficientStockError
from inventory_service.infrastructure.idempotency import SqlAlchemyIdempotencyStore
from inventory_service.infrastructure.repositories import SqlAlchemyInventoryRepository


class InventoryConsumer:
    def __init__(
        self,
        rabbitmq_url: str,
        exchange_name: str,
        session_factory: async_sessionmaker,
        lock_factory: Callable[[], object] | None = None,
    ) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._exchange_name = exchange_name
        self._session_factory = session_factory
        self._lock_factory = lock_factory
        self._connection: aio_pika.RobustConnection | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=10)
        self._exchange = await channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue("inventory.events", durable=True)
        await queue.bind(self._exchange, routing_key="order.created")
        await queue.bind(self._exchange, routing_key="inventory.released")
        await queue.consume(self._on_message)

    async def _on_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process(requeue=True):
            event = deserialize_event(json.loads(message.body))
            async with self._session_factory() as session:
                idempotency = SqlAlchemyIdempotencyStore(session)
                repository = SqlAlchemyInventoryRepository(session)
                lock = self._lock_factory() if self._lock_factory else None
                service = InventoryService(repository, lock)

                if isinstance(event, OrderCreated):
                    await self._handle_order_created(event, service, idempotency)
                elif isinstance(event, InventoryReleased):
                    await self._handle_release(event, service, idempotency)

    async def _handle_order_created(self, event: OrderCreated, service, idempotency) -> None:
        if await idempotency.is_processed(event.event_id):
            return
        reserved: list = []
        try:
            for item in event.items:
                await service.reserve(item.product_id, item.quantity)
                reserved.append(item)
        except InsufficientStockError as exc:
            for item in reserved:
                await service.release(item.product_id, item.quantity)
            await self._publish(
                InventoryReservationFailed(
                    correlation_id=event.correlation_id,
                    order_id=event.order_id,
                    reason=str(exc),
                )
            )
            await idempotency.mark_processed(event.event_id)
            return

        await self._publish(
            InventoryReserved(
                correlation_id=event.correlation_id,
                order_id=event.order_id,
                items=[i.model_dump() for i in event.items],
            )
        )
        await idempotency.mark_processed(event.event_id)

    async def _handle_release(self, event: InventoryReleased, service, idempotency) -> None:
        if await idempotency.is_processed(event.event_id):
            return
        for item in event.items:
            await service.release(item.product_id, item.quantity)
        await idempotency.mark_processed(event.event_id)

    async def _publish(self, event) -> None:
        assert self._exchange is not None
        await self._exchange.publish(
            aio_pika.Message(
                body=event.model_dump_json().encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=event.type,
        )

    async def stop(self) -> None:
        if self._connection is not None:
            await self._connection.close()
