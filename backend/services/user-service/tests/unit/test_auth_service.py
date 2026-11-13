"""Unit tests for the AuthService use cases with fakes."""

from __future__ import annotations

import pytest

from shop_shared.errors import ConflictError, NotFoundError, UnauthorizedError

from user_service.application.auth_service import AuthService
from tests.unit.fakes import FakeHasher, FakeTokens, FakeUserRepository


@pytest.fixture
def service():
    repo = FakeUserRepository()
    return AuthService(repo, FakeHasher(), FakeTokens()), repo


async def test_register_creates_user(service):
    auth, repo = service
    user = await auth.register("foo@bar.com", "password123", "Foo")
    assert user.email == "foo@bar.com"
    assert (await repo.get_by_email("foo@bar.com")) is not None


async def test_register_duplicate_email_raises(service):
    auth, _ = service
    await auth.register("foo@bar.com", "password123")
    with pytest.raises(ConflictError):
        await auth.register("FOO@bar.com", "password123")


async def test_login_returns_token(service):
    auth, _ = service
    await auth.register("foo@bar.com", "password123")
    token = await auth.login("foo@bar.com", "password123")
    assert token == "token:user" or token.startswith("token:")


async def test_login_wrong_password_raises(service):
    auth, _ = service
    await auth.register("foo@bar.com", "password123")
    with pytest.raises(UnauthorizedError):
        await auth.login("foo@bar.com", "wrong-password")


async def test_login_unknown_email_raises(service):
    auth, _ = service
    with pytest.raises(UnauthorizedError):
        await auth.login("nobody@bar.com", "password123")


async def test_get_me_returns_user(service):
    auth, _ = service
    user = await auth.register("foo@bar.com", "password123")
    found = await auth.get_me(user.id)
    assert found.id == user.id


async def test_get_me_unknown_raises(service):
    auth, _ = service
    with pytest.raises(NotFoundError):
        await auth.get_me("missing-id")
