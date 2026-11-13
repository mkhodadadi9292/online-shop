"""Production entrypoint: create tables, connect publisher, start the saga
consumer, and run the HTTP server."""

from __future__ import annotations

import asyncio
import os

import uvicorn

from order_service.api.main import create_app
from order_service.config import Settings
from order_service.infrastructure.catalog_client import HttpCatalogClient
from order_service.infrastructure.consumer import OrderSagaConsumer
from order_service.infrastructure.db import Base
from order_service.infrastructure.publisher import RabbitMQEventPublisher


async def main() -> None:
    settings = Settings()
    publisher = RabbitMQEventPublisher(settings.rabbitmq_url, settings.events_exchange)
    catalog = HttpCatalogClient(settings.catalog_service_url)
    app = create_app(settings, publisher=publisher, catalog_client=catalog)
    async with app.state.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await publisher.connect()
    consumer = OrderSagaConsumer(
        settings.rabbitmq_url,
        settings.events_exchange,
        app.state.session_factory,
        publisher,
    )
    await consumer.start()

    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), log_level="info")
    await uvicorn.Server(config).serve()

    await consumer.stop()
    await publisher.close()
    await catalog.close()


if __name__ == "__main__":
    asyncio.run(main())
