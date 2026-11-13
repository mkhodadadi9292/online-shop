"""Inventory endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from inventory_service.api.deps import get_inventory_service
from inventory_service.api.schemas import (
    AdjustRequest,
    CreateInventoryRequest,
    InventoryResponse,
    ReleaseRequest,
    ReserveRequest,
)
from inventory_service.application.inventory_service import InventoryService
from inventory_service.domain.inventory import InventoryItem

router = APIRouter(tags=["inventory"])


def _response(item: InventoryItem) -> InventoryResponse:
    return InventoryResponse(
        product_id=item.product_id,
        stock=item.stock,
        reserved=item.reserved,
    )


@router.get("/{product_id}", response_model=InventoryResponse)
async def get_inventory(
    product_id: str,
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryResponse:
    return _response(await service.get(product_id))


@router.post("", response_model=InventoryResponse, status_code=201)
async def create_inventory(
    payload: CreateInventoryRequest,
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryResponse:
    return _response(await service.create(payload.product_id, payload.stock))


@router.post("/{product_id}/reserve", response_model=InventoryResponse)
async def reserve(
    product_id: str,
    payload: ReserveRequest,
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryResponse:
    return _response(await service.reserve(product_id, payload.quantity))


@router.post("/{product_id}/release", response_model=InventoryResponse)
async def release(
    product_id: str,
    payload: ReleaseRequest,
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryResponse:
    return _response(await service.release(product_id, payload.quantity))


@router.post("/{product_id}/adjust", response_model=InventoryResponse)
async def adjust(
    product_id: str,
    payload: AdjustRequest,
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryResponse:
    return _response(await service.adjust_stock(product_id, payload.delta))
