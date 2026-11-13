"""Payment aggregate (pure, stdlib only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Payment:
    id: str
    order_id: str
    amount: int  # minor units
    status: PaymentStatus
    reference: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, order_id: str, amount: int) -> "Payment":
        return cls(id=str(uuid4()), order_id=order_id, amount=amount, status=PaymentStatus.PENDING)

    def complete(self, reference: str) -> None:
        self.status = PaymentStatus.COMPLETED
        self.reference = reference

    def fail(self) -> None:
        self.status = PaymentStatus.FAILED

    def refund(self) -> None:
        self.status = PaymentStatus.REFUNDED
