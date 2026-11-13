"""Adapters that satisfy the PasswordHasher and TokenService ports."""

from __future__ import annotations

from shop_shared import auth as auth_utils

from user_service.config import Settings


class BcryptPasswordHasher:
    def hash(self, password: str) -> str:
        return auth_utils.hash_password(password)

    def verify(self, password: str, hashed: str) -> bool:
        return auth_utils.verify_password(password, hashed)


class JwtTokenService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create(self, subject: str) -> str:
        return auth_utils.create_access_token(
            subject=subject,
            secret=self._settings.jwt_secret,
            algorithm=self._settings.jwt_algorithm,
            expires_minutes=self._settings.jwt_expire_minutes,
        )

    def decode(self, token: str) -> dict:
        return auth_utils.decode_access_token(
            token=token,
            secret=self._settings.jwt_secret,
            algorithm=self._settings.jwt_algorithm,
        )
