"""Domain layer — pure entities and value objects with no infrastructure deps."""

from user_service.domain.user import Email, User

__all__ = ["Email", "User"]
