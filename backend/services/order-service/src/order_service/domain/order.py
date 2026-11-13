"""Order aggregate and saga state (pure, stdlib only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class OrderStatus(str, Enum):
    PENDING = "pending"
    RESERVING = "reserving"
    PAYING = "paying"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class OrderItem:
    product_id: str
    quantity: int
    unit_price: int


@dataclass
class Order:
    id: str
    user_id: str
    items: list[OrderItem]
    total_amount: int
    status: OrderStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, user_id: str, items: list[OrderItem]) -> "Order":
        total = sum(item.unit_price * item.quantity for item in items)
        return cls(
            id=str(uuid4()),
            user_id=user_id,
            items=items,
            total_amount=total,
            status=OrderStatus.PENDING,
        )

    def mark_reserving(self) -> None:
        self.status = OrderStatus.RESERVING

    def mark_paying(self) -> None:
        self.status = OrderStatus.PAYING

    def confirm(self) -> None:
        self.status = OrderStatus.CONFIRMED

    def cancel(self) -> None:
        self.status = OrderStatus.CANCELLED
