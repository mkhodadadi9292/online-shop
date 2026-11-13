"""FastAPI dependency wiring."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from inventory_service.application.inventory_service import InventoryService
from inventory_service.infrastructure.repositories import SqlAlchemyInventoryRepository


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_inventory_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> InventoryService:
    repository = SqlAlchemyInventoryRepository(session)
    lock = getattr(request.app.state, "lock", None)
    return InventoryService(repository, lock)
