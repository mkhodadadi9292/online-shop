"""Production entrypoint: create tables (MVP) and run the HTTP server."""

from __future__ import annotations

import asyncio
import os

import uvicorn

from user_service.api.main import create_app
from user_service.config import Settings
from user_service.infrastructure.db import Base


async def main() -> None:
    app = create_app(Settings())
    async with app.state.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), log_level="info")
    await uvicorn.Server(config).serve()


if __name__ == "__main__":
    asyncio.run(main())
