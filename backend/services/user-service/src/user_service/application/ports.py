"""Ports (interfaces) the application layer depends on.

Defined as Protocols so any infrastructure implementation can satisfy them and
tests can substitute in-memory fakes. This is the seam that makes unit testing
the use cases trivial without a database.
"""

from __future__ import annotations

from typing import Protocol

from user_service.domain.user import User


class UserRepository(Protocol):
    async def get_by_id(self, user_id: str) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def add(self, user: User) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, hashed: str) -> bool: ...


class TokenService(Protocol):
    def create(self, subject: str) -> str: ...

    def decode(self, token: str) -> dict: ...
