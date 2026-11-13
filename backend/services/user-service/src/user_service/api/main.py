"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shop_shared.errors import (
    ConflictError,
    NotFoundError,
    ShopError,
    UnauthorizedError,
)

from user_service.api.routes.auth import router as auth_router
from user_service.api.schemas import ErrorResponse
from user_service.config import Settings
from user_service.domain.user import InvalidEmailError
from user_service.infrastructure.db import create_engine, create_session_factory
from user_service.infrastructure.security import BcryptPasswordHasher, JwtTokenService

_STATUS_BY_ERROR: dict[type[ShopError], int] = {
    ConflictError: 409,
    UnauthorizedError: 401,
    NotFoundError: 404,
}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    app = FastAPI(title="User Service", version="0.1.0")

    app.state.settings = settings
    app.state.engine = create_engine(settings.database_url)
    app.state.session_factory = create_session_factory(app.state.engine)
    app.state.hasher = BcryptPasswordHasher()
    app.state.tokens = JwtTokenService(settings)

    app.include_router(auth_router, prefix="/api/users")

    @app.exception_handler(ShopError)
    async def handle_shop_error(request: Request, exc: ShopError) -> JSONResponse:
        status_code = _STATUS_BY_ERROR.get(type(exc), 400)
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(code=exc.code, message=exc.message).model_dump(),
        )

    @app.exception_handler(InvalidEmailError)
    async def handle_invalid_email(request: Request, exc: InvalidEmailError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(code="validation_error", message=str(exc)).model_dump(),
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
