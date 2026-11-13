"""End-to-end HTTP tests for the inventory API."""

from __future__ import annotations

import httpx
import pytest

from inventory_service.api.main import create_app
from inventory_service.config import Settings
from tests.conftest import TEST_DATABASE_URL


@pytest.fixture
async def client(engine):
    settings = Settings(database_url=TEST_DATABASE_URL)
    app = create_app(settings, lock=None)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await app.state.engine.dispose()


async def test_create_reserve_get(client):
    create = await client.post("/api/inventory", json={"product_id": "p1", "stock": 10})
    assert create.status_code == 201

    reserve = await client.post("/api/inventory/p1/reserve", json={"quantity": 3})
    assert reserve.status_code == 200
    assert reserve.json()["stock"] == 7
    assert reserve.json()["reserved"] == 3

    got = await client.get("/api/inventory/p1")
    assert got.json()["stock"] == 7


async def test_reserve_insufficient_returns_409(client):
    await client.post("/api/inventory", json={"product_id": "p1", "stock": 1})
    response = await client.post("/api/inventory/p1/reserve", json={"quantity": 2})
    assert response.status_code == 409
    assert response.json()["code"] == "insufficient_stock"


async def test_get_missing_returns_404(client):
    response = await client.get("/api/inventory/missing")
    assert response.status_code == 404
