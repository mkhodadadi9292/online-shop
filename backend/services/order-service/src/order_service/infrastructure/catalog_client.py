"""HTTP client for the Catalog Service (synchronous read path)."""

from __future__ import annotations

import httpx

from order_service.application.ports import ProductInfo


class HttpCatalogClient:
    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url)

    async def get_product(self, product_id: str) -> ProductInfo | None:
        response = await self._client.get(f"/api/products/{product_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return ProductInfo(
            product_id=data["id"],
            name=data["name"],
            price=data["price"],
        )

    async def close(self) -> None:
        await self._client.aclose()
