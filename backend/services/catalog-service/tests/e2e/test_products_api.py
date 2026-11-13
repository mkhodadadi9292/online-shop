"""End-to-end HTTP tests for the products API."""

from __future__ import annotations

import httpx
import pytest

from catalog_service.api.main import create_app
from catalog_service.config import Settings
from tests.conftest import TEST_DATABASE_URL


@pytest.fixture
async def client(engine):
    settings = Settings(database_url=TEST_DATABASE_URL)
    app = create_app(settings)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await app.state.engine.dispose()


async def test_create_list_get_flow(client):
    create = await client.post(
        "/api/products",
        json={"name": "Widget", "description": "desc", "price": 1000, "category": "tools"},
    )
    assert create.status_code == 201
    product_id = create.json()["id"]

    listed = await client.get("/api/products", params={"category": "tools"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    got = await client.get(f"/api/products/{product_id}")
    assert got.status_code == 200
    assert got.json()["name"] == "Widget"


async def test_get_missing_returns_404(client):
    response = await client.get("/api/products/missing")
    assert response.status_code == 404


async def test_create_negative_price_returns_422(client):
    response = await client.post(
        "/api/products",
        json={"name": "Bad", "description": "", "price": -1, "category": "x"},
    )
    assert response.status_code == 422
