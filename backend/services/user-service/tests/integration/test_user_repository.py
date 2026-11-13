"""Integration tests for the SQLAlchemy user repository against real Postgres."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from user_service.domain.user import User
from user_service.infrastructure.repositories import SqlAlchemyUserRepository


async def test_add_and_fetch_by_email(session):
    repo = SqlAlchemyUserRepository(session)
    user = User.create("foo@bar.com", "hashed", "Foo")
    await repo.add(user)
    await session.commit()

    fetched = await repo.get_by_email("FOO@bar.com")
    assert fetched is not None
    assert fetched.id == user.id


async def test_get_by_id_missing_returns_none(session):
    repo = SqlAlchemyUserRepository(session)
    assert await repo.get_by_id("missing") is None


async def test_duplicate_email_raises_integrity_error(session):
    repo = SqlAlchemyUserRepository(session)
    await repo.add(User.create("dup@bar.com", "hashed"))
    await session.commit()

    with pytest.raises(IntegrityError):
        await repo.add(User.create("dup@bar.com", "hashed"))
        await session.commit()
