"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    price: int = Field(ge=0)
    category: str = Field(min_length=1, max_length=120)
    image_url: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: int | None = Field(default=None, ge=0)
    category: str | None = None
    image_url: str | None = None


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    price: int
    category: str
    image_url: str | None
    created_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    code: str
    message: str
