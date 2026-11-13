"""Domain-agnostic error types shared across services."""

from __future__ import annotations


class ShopError(Exception):
    """Base error with a machine-readable code used in HTTP/event responses."""

    code = "shop_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ShopError):
    code = "not_found"


class ConflictError(ShopError):
    code = "conflict"


class ValidationError(ShopError):
    code = "validation_error"


class UnauthorizedError(ShopError):
    code = "unauthorized"


class InsufficientStockError(ShopError):
    code = "insufficient_stock"


class PaymentError(ShopError):
    code = "payment_error"


class SagaError(ShopError):
    code = "saga_error"
