"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shop_shared.errors import ConflictError, NotFoundError, PaymentError, ShopError

from payment_service.api.routes.payments import router as payments_router
from payment_service.api.schemas import ErrorResponse
from payment_service.application.ports import PaymentGateway
from payment_service.config import Settings
from payment_service.infrastructure.db import create_engine, create_session_factory
from payment_service.infrastructure.gateway import MockPaymentGateway


def create_app(
    settings: Settings | None = None,
    gateway: PaymentGateway | None = None,
) -> FastAPI:
    settings = settings or Settings()

    app = FastAPI(title="Payment Service", version="0.1.0")

    app.state.settings = settings
    app.state.engine = create_engine(settings.database_url)
    app.state.session_factory = create_session_factory(app.state.engine)
    app.state.gateway = gateway or MockPaymentGateway()

    app.include_router(payments_router, prefix="/api/payments")

    @app.exception_handler(ShopError)
    async def handle_shop_error(request: Request, exc: ShopError) -> JSONResponse:
        status_code = {NotFoundError: 404, ConflictError: 409, PaymentError: 400}.get(
            type(exc), 400
        )
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(code=exc.code, message=exc.message).model_dump(),
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
