"""FastAPI dependency wiring."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from order_service.application.order_service import OrderService
from order_service.infrastructure.repositories import SqlAlchemyOrderRepository


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_order_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> OrderService:
    repository = SqlAlchemyOrderRepository(session)
    return OrderService(
        repository,
        request.app.state.publisher,
        request.app.state.catalog_client,
    )
