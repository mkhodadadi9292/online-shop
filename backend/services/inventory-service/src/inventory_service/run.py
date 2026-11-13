"""Production entrypoint: create tables, start the saga consumer, run HTTP."""

from __future__ import annotations

import asyncio
import os

import uvicorn

from inventory_service.api.main import create_app
from inventory_service.config import Settings
from inventory_service.infrastructure.consumer import InventoryConsumer
from inventory_service.infrastructure.db import Base
from inventory_service.infrastructure.locking import RedisDistributedLock


async def main() -> None:
    settings = Settings()
    app = create_app(settings, lock=RedisDistributedLock(settings.redis_url))
    async with app.state.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    consumer = InventoryConsumer(
        settings.rabbitmq_url,
        settings.events_exchange,
        app.state.session_factory,
    )
    await consumer.start()

    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), log_level="info")
    await uvicorn.Server(config).serve()

    await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
