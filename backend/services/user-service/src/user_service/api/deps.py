"""FastAPI dependency wiring."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from shop_shared.errors import UnauthorizedError

from user_service.application.auth_service import AuthService
from user_service.application.ports import PasswordHasher, TokenService
from user_service.infrastructure.repositories import SqlAlchemyUserRepository


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_auth_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    hasher: PasswordHasher = request.app.state.hasher
    tokens: TokenService = request.app.state.tokens
    repository = SqlAlchemyUserRepository(session)
    return AuthService(repository, hasher, tokens)


async def get_current_user_id(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    if not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    tokens: TokenService = request.app.state.tokens
    try:
        payload = tokens.decode(token)
    except Exception:
        raise UnauthorizedError("Invalid or expired token") from None
    return payload["sub"]
