"""RabbitMQ consumer for the payment saga participant."""

from __future__ import annotations

import json

import aio_pika

from shop_shared.events import (
    PaymentCompleted,
    PaymentFailed,
    PaymentRequested,
    deserialize_event,
)
from shop_shared.errors import PaymentError
from sqlalchemy.ext.asyncio import async_sessionmaker

from payment_service.application.payment_service import PaymentService
from payment_service.application.ports import PaymentGateway
from payment_service.domain.payment import PaymentStatus
from payment_service.infrastructure.idempotency import SqlAlchemyIdempotencyStore
from payment_service.infrastructure.repositories import SqlAlchemyPaymentRepository


class PaymentConsumer:
    def __init__(
        self,
        rabbitmq_url: str,
        exchange_name: str,
        session_factory: async_sessionmaker,
        gateway: PaymentGateway,
    ) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._exchange_name = exchange_name
        self._session_factory = session_factory
        self._gateway = gateway
        self._connection: aio_pika.RobustConnection | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=10)
        self._exchange = await channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue("payment.events", durable=True)
        await queue.bind(self._exchange, routing_key="payment.requested")
        await queue.consume(self._on_message)

    async def _on_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process(requeue=True):
            event = deserialize_event(json.loads(message.body))
            if not isinstance(event, PaymentRequested):
                return

            async with self._session_factory() as session:
                idempotency = SqlAlchemyIdempotencyStore(session)
                if await idempotency.is_processed(event.event_id):
                    return

                service = PaymentService(
                    SqlAlchemyPaymentRepository(session), self._gateway
                )
                payment = await service.process(event.order_id, event.amount)

                if payment.status == PaymentStatus.COMPLETED:
                    await self._publish(
                        PaymentCompleted(
                            correlation_id=event.correlation_id,
                            order_id=event.order_id,
                            payment_id=payment.id,
                        )
                    )
                else:
                    await self._publish(
                        PaymentFailed(
                            correlation_id=event.correlation_id,
                            order_id=event.order_id,
                            reason="Payment failed",
                        )
                    )
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
