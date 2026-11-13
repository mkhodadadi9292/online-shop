"""User aggregate and Email value object.

The domain layer is pure: it depends only on the standard library. It knows
nothing about SQLAlchemy, FastAPI, or the shared package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


class InvalidEmailError(ValueError):
    """Raised when an email fails validation."""


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise InvalidEmailError(f"Invalid email address: {self.value!r}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass
class User:
    id: str
    email: str
    hashed_password: str
    full_name: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
    ) -> "User":
        validated = Email(email)
        return cls(
            id=str(uuid4()),
            email=validated.value,
            hashed_password=hashed_password,
            full_name=full_name,
        )
