"""Order endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from order_service.api.deps import get_order_service
from order_service.api.schemas import (
    CreateOrderRequest,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
)
from order_service.application.order_service import OrderService
from order_service.domain.order import Order

router = APIRouter(tags=["orders"])


def _response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        items=[OrderItemResponse(**i.__dict__) for i in order.items],
        total_amount=order.total_amount,
        status=order.status.value,
        created_at=order.created_at,
    )


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    payload: CreateOrderRequest,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    items = [{"product_id": i.product_id, "quantity": i.quantity} for i in payload.items]
    order = await service.create_order(payload.user_id, items)
    return _response(order)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    user_id: str,
    service: OrderService = Depends(get_order_service),
) -> OrderListResponse:
    orders = await service.list_orders(user_id)
    return OrderListResponse(items=[_response(o) for o in orders])


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    return _response(await service.get_order(order_id))
