"""RabbitMQ consumer for the order saga orchestrator.

Consumes the saga reply events and dispatches them to the OrderSaga state machine,
deduplicating on event_id.
"""

from __future__ import annotations

import json

import aio_pika

from shop_shared.events import (
    InventoryReservationFailed,
    InventoryReserved,
    PaymentCompleted,
    PaymentFailed,
    deserialize_event,
)
from sqlalchemy.ext.asyncio import async_sessionmaker

from order_service.application.ports import EventPublisher
from order_service.application.saga import OrderSaga
from order_service.infrastructure.idempotency import SqlAlchemyIdempotencyStore
from order_service.infrastructure.repositories import SqlAlchemyOrderRepository


class OrderSagaConsumer:
    def __init__(
        self,
        rabbitmq_url: str,
        exchange_name: str,
        session_factory: async_sessionmaker,
        publisher: EventPublisher,
    ) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._exchange_name = exchange_name
        self._session_factory = session_factory
        self._publisher = publisher
        self._connection: aio_pika.RobustConnection | None = None

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=10)
        exchange = await channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue("order.saga.events", durable=True)
        for key in (
            "inventory.reserved",
            "inventory.reservation_failed",
            "payment.completed",
            "payment.failed",
        ):
            await queue.bind(exchange, routing_key=key)
        await queue.consume(self._on_message)

    async def _on_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process(requeue=True):
            event = deserialize_event(json.loads(message.body))
            async with self._session_factory() as session:
                idempotency = SqlAlchemyIdempotencyStore(session)
                if await idempotency.is_processed(event.event_id):
                    return

                saga = OrderSaga(
                    SqlAlchemyOrderRepository(session), self._publisher
                )

                if isinstance(event, InventoryReserved):
                    await saga.handle_inventory_reserved(event)
                elif isinstance(event, InventoryReservationFailed):
                    await saga.handle_inventory_reservation_failed(event)
                elif isinstance(event, PaymentCompleted):
                    await saga.handle_payment_completed(event)
                elif isinstance(event, PaymentFailed):
                    await saga.handle_payment_failed(event)

                await idempotency.mark_processed(event.event_id)

    async def stop(self) -> None:
        if self._connection is not None:
            await self._connection.close()
