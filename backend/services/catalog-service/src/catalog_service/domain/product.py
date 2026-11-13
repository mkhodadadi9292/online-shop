"""Product aggregate and Price value object (pure, stdlib only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


class InvalidPriceError(ValueError):
    pass


@dataclass(frozen=True)
class Price:
    value: int  # integer minor units (cents)

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidPriceError("Price cannot be negative")


@dataclass
class Product:
    id: str
    name: str
    description: str
    price: int
    category: str
    image_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        price: int,
        category: str,
        image_url: str | None = None,
    ) -> "Product":
        validated_price = Price(price)
        return cls(
            id=str(uuid4()),
            name=name,
            description=description,
            price=validated_price.value,
            category=category,
            image_url=image_url,
        )

    def change_price(self, new_price: int) -> None:
        self.price = Price(new_price).value
