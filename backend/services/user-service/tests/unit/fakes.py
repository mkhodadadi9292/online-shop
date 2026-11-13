"""In-memory fakes for the application ports (unit tests only)."""

from __future__ import annotations

from user_service.domain.user import User


class FakeUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, User] = {}
        self._by_email: dict[str, User] = {}

    async def get_by_id(self, user_id: str) -> User | None:
        return self._by_id.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return self._by_email.get(email.strip().lower())

    async def add(self, user: User) -> None:
        self._by_id[user.id] = user
        self._by_email[user.email] = user


class FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"


class FakeTokens:
    def create(self, subject: str) -> str:
        return f"token:{subject}"

    def decode(self, token: str) -> dict:
        return {"sub": token.split(":", 1)[1]}
