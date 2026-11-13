"""FastAPI dependency wiring."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from catalog_service.application.catalog_service import CatalogService
from catalog_service.infrastructure.repositories import SqlAlchemyProductRepository


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_catalog_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> CatalogService:
    repository = SqlAlchemyProductRepository(session)
    return CatalogService(repository)
