"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shop_shared.errors import ConflictError, NotFoundError, ShopError

from inventory_service.api.routes.inventory import router as inventory_router
from inventory_service.api.schemas import ErrorResponse
from inventory_service.application.ports import DistributedLock
from inventory_service.config import Settings
from inventory_service.domain.inventory import (
    InsufficientStockError,
    InvalidQuantityError,
)
from inventory_service.infrastructure.db import create_engine, create_session_factory
from inventory_service.infrastructure.locking import NoopLock


def create_app(
    settings: Settings | None = None,
    lock: DistributedLock | None = None,
) -> FastAPI:
    settings = settings or Settings()

    app = FastAPI(title="Inventory Service", version="0.1.0")

    app.state.settings = settings
    app.state.engine = create_engine(settings.database_url)
    app.state.session_factory = create_session_factory(app.state.engine)
    app.state.lock = lock or NoopLock()

    app.include_router(inventory_router, prefix="/api/inventory")

    @app.exception_handler(ShopError)
    async def handle_shop_error(request: Request, exc: ShopError) -> JSONResponse:
        status_code = {NotFoundError: 404, ConflictError: 409}.get(type(exc), 400)
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(code=exc.code, message=exc.message).model_dump(),
        )

    @app.exception_handler(InsufficientStockError)
    async def handle_insufficient(request: Request, exc: InsufficientStockError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=ErrorResponse(code="insufficient_stock", message=str(exc)).model_dump(),
        )

    @app.exception_handler(InvalidQuantityError)
    async def handle_invalid_quantity(request: Request, exc: InvalidQuantityError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(code="validation_error", message=str(exc)).model_dump(),
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
