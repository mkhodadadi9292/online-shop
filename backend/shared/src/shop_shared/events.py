"""Event contracts for the saga message flow.

These are the single source of truth for the asynchronous part of the system.
Every event carries a correlation_id (ties it to one order/saga instance) and an
event_id (used for idempotent consumption). Amounts are integer minor units
(cents) to avoid floating-point drift across service boundaries.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: str
    type: str
    version: int = 1
    occurred_at: datetime = Field(default_factory=_now)


class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(ge=0)


class OrderCreated(Event):
    type: str = "order.created"
    order_id: str
    user_id: str
    items: list[OrderItem]
    total_amount: int


class InventoryReserved(Event):
    type: str = "inventory.reserved"
    order_id: str
    items: list[OrderItem]


class InventoryReservationFailed(Event):
    type: str = "inventory.reservation_failed"
    order_id: str
    reason: str


class InventoryReleased(Event):
    type: str = "inventory.released"
    order_id: str
    items: list[OrderItem]


class PaymentRequested(Event):
    type: str = "payment.requested"
    order_id: str
    amount: int


class PaymentCompleted(Event):
    type: str = "payment.completed"
    order_id: str
    payment_id: str


class PaymentFailed(Event):
    type: str = "payment.failed"
    order_id: str
    reason: str


class OrderConfirmed(Event):
    type: str = "order.confirmed"
    order_id: str


class OrderCancelled(Event):
    type: str = "order.cancelled"
    order_id: str
    reason: str


EVENT_REGISTRY: dict[str, type[Event]] = {
    cls.model_fields["type"].default: cls  # type: ignore[attr-defined]
    for cls in (
        OrderCreated,
        InventoryReserved,
        InventoryReservationFailed,
        InventoryReleased,
        PaymentRequested,
        PaymentCompleted,
        PaymentFailed,
        OrderConfirmed,
        OrderCancelled,
    )
}


def deserialize_event(data: dict[str, Any]) -> Event:
    """Rebuild the correct event subclass from a raw message dict."""
    event_type = data.get("type")
    model = EVENT_REGISTRY.get(event_type)
    if model is None:
        raise ValueError(f"Unknown event type: {event_type!r}")
    return model.model_validate(data)
