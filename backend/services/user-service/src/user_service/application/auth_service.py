"""Authentication use cases: register, login, and current-user lookup."""

from __future__ import annotations

from shop_shared.errors import ConflictError, NotFoundError, UnauthorizedError

from user_service.application.ports import PasswordHasher, TokenService, UserRepository
from user_service.domain.user import User


class AuthService:
    def __init__(
        self,
        repository: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
    ) -> None:
        self._repository = repository
        self._hasher = hasher
        self._tokens = tokens

    async def register(
        self,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> User:
        existing = await self._repository.get_by_email(email)
        if existing is not None:
            raise ConflictError("An account with this email already exists")

        user = User.create(
            email=email,
            hashed_password=self._hasher.hash(password),
            full_name=full_name,
        )
        await self._repository.add(user)
        return user

    async def login(self, email: str, password: str) -> str:
        user = await self._repository.get_by_email(email)
        if user is None or not self._hasher.verify(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        return self._tokens.create(user.id)

    async def get_me(self, user_id: str) -> User:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user
