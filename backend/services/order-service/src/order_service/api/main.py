"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shop_shared.errors import NotFoundError, ShopError, ValidationError

from order_service.api.routes.orders import router as orders_router
from order_service.api.schemas import ErrorResponse
from order_service.application.ports import CatalogClient, EventPublisher
from order_service.config import Settings
from order_service.infrastructure.catalog_client import HttpCatalogClient
from order_service.infrastructure.db import create_engine, create_session_factory


class _UnconfiguredPublisher:
    async def publish(self, event) -> None:
        raise RuntimeError("Event publisher is not configured")


def create_app(
    settings: Settings | None = None,
    publisher: EventPublisher | None = None,
    catalog_client: CatalogClient | None = None,
) -> FastAPI:
    settings = settings or Settings()

    app = FastAPI(title="Order Service", version="0.1.0")

    app.state.settings = settings
    app.state.engine = create_engine(settings.database_url)
    app.state.session_factory = create_session_factory(app.state.engine)
    app.state.publisher = publisher or _UnconfiguredPublisher()
    app.state.catalog_client = catalog_client or HttpCatalogClient(settings.catalog_service_url)

    app.include_router(orders_router, prefix="/api/orders")

    @app.exception_handler(ShopError)
    async def handle_shop_error(request: Request, exc: ShopError) -> JSONResponse:
        status_code = {NotFoundError: 404, ValidationError: 422}.get(type(exc), 400)
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(code=exc.code, message=exc.message).model_dump(),
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
