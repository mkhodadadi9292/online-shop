"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreateOrderItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    user_id: str
    items: list[CreateOrderItem] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    product_id: str
    quantity: int
    unit_price: int


class OrderResponse(BaseModel):
    id: str
    user_id: str
    items: list[OrderItemResponse]
    total_amount: int
    status: str
    created_at: datetime


class OrderListResponse(BaseModel):
    items: list[OrderResponse]


class ErrorResponse(BaseModel):
    code: str
    message: str
