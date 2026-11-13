"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shop_shared.errors import NotFoundError, ShopError

from catalog_service.api.routes.products import router as products_router
from catalog_service.api.schemas import ErrorResponse
from catalog_service.config import Settings
from catalog_service.domain.product import InvalidPriceError
from catalog_service.infrastructure.db import create_engine, create_session_factory

_STATUS_BY_ERROR: dict[type[ShopError], int] = {
    NotFoundError: 404,
}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    app = FastAPI(title="Catalog Service", version="0.1.0")

    app.state.settings = settings
    app.state.engine = create_engine(settings.database_url)
    app.state.session_factory = create_session_factory(app.state.engine)

    app.include_router(products_router, prefix="/api/products")

    @app.exception_handler(ShopError)
    async def handle_shop_error(request: Request, exc: ShopError) -> JSONResponse:
        status_code = _STATUS_BY_ERROR.get(type(exc), 400)
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(code=exc.code, message=exc.message).model_dump(),
        )

    @app.exception_handler(InvalidPriceError)
    async def handle_invalid_price(request: Request, exc: InvalidPriceError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(code="validation_error", message=str(exc)).model_dump(),
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
