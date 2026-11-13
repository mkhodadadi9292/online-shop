"""Production entrypoint: create tables, start the saga consumer, run HTTP."""

from __future__ import annotations

import asyncio
import os

import uvicorn

from payment_service.api.main import create_app
from payment_service.config import Settings
from payment_service.infrastructure.consumer import PaymentConsumer
from payment_service.infrastructure.db import Base
from payment_service.infrastructure.gateway import MockPaymentGateway


async def main() -> None:
    settings = Settings()
    gateway = MockPaymentGateway(decline_amount=settings.decline_amount)
    app = create_app(settings, gateway=gateway)
    async with app.state.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    consumer = PaymentConsumer(
        settings.rabbitmq_url,
        settings.events_exchange,
        app.state.session_factory,
        gateway,
    )
    await consumer.start()

    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), log_level="info")
    await uvicorn.Server(config).serve()

    await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
