"""Product endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from catalog_service.api.deps import get_catalog_service
from catalog_service.api.schemas import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from catalog_service.application.catalog_service import CatalogService
from catalog_service.application.ports import ProductFilter
from catalog_service.domain.product import Product

router = APIRouter(tags=["products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    search: str | None = None,
    category: str | None = None,
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    sort: str | None = Query(default=None, pattern="^(price_asc|price_desc|newest)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: CatalogService = Depends(get_catalog_service),
) -> ProductListResponse:
    page_result = await service.list_products(
        ProductFilter(
            search=search,
            category=category,
            min_price=min_price,
            max_price=max_price,
            sort=sort,
            page=page,
            page_size=page_size,
        )
    )
    return ProductListResponse(
        items=[ProductResponse.model_validate(p, from_attributes=True) for p in page_result.items],
        total=page_result.total,
        page=page_result.page,
        page_size=page_result.page_size,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    service: CatalogService = Depends(get_catalog_service),
) -> Product:
    return await service.get_product(product_id)


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    payload: ProductCreate,
    service: CatalogService = Depends(get_catalog_service),
) -> Product:
    return await service.create_product(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        category=payload.category,
        image_url=payload.image_url,
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    service: CatalogService = Depends(get_catalog_service),
) -> Product:
    return await service.update_product(
        product_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        category=payload.category,
        image_url=payload.image_url,
    )


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    service: CatalogService = Depends(get_catalog_service),
) -> None:
    await service.delete_product(product_id)
