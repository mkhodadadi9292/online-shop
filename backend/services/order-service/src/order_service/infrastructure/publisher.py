"""RabbitMQ event publisher."""

from __future__ import annotations

import aio_pika

from shop_shared.events import Event


class RabbitMQEventPublisher:
    def __init__(self, rabbitmq_url: str, exchange_name: str) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._exchange_name = exchange_name
        self._connection: aio_pika.RobustConnection | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        channel = await self._connection.channel()
        self._exchange = await channel.declare_exchange(
            self._exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def publish(self, event: Event) -> None:
        assert self._exchange is not None, "publisher not connected"
        await self._exchange.publish(
            aio_pika.Message(
                body=event.model_dump_json().encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=event.type,
        )

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
