"""DB-backed idempotency store for message consumers.

mark_processed uses INSERT ... ON CONFLICT DO NOTHING so concurrent deliveries of
the same event are safe: exactly one caller "wins" and actually processes it.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from inventory_service.infrastructure.models import ProcessedEventModel


class SqlAlchemyIdempotencyStore:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def is_processed(self, key: str) -> bool:
        result = await self._session.execute(
            select(ProcessedEventModel).where(ProcessedEventModel.event_id == key)
        )
        return result.scalar_one_or_none() is not None

    async def mark_processed(self, key: str) -> bool:
        """Return True if this call newly marked the key (first processing)."""
        stmt = (
            pg_insert(ProcessedEventModel)
            .values(event_id=key)
            .on_conflict_do_nothing(index_elements=["event_id"])
            .returning(ProcessedEventModel.event_id)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.scalar_one_or_none() is not None
