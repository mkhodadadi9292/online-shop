"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    amount: int
    status: str
    reference: str | None
    created_at: datetime


class ProcessPaymentRequest(BaseModel):
    order_id: str
    amount: int = Field(gt=0)


class ErrorResponse(BaseModel):
    code: str
    message: str
