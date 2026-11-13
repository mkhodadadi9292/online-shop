"""Pydantic request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InventoryResponse(BaseModel):
    product_id: str
    stock: int
    reserved: int


class CreateInventoryRequest(BaseModel):
    product_id: str
    stock: int = Field(ge=0)


class ReserveRequest(BaseModel):
    quantity: int = Field(gt=0)


class ReleaseRequest(BaseModel):
    quantity: int = Field(gt=0)


class AdjustRequest(BaseModel):
    delta: int


class ErrorResponse(BaseModel):
    code: str
    message: str
