"""End-to-end HTTP tests for the orders API (fakes for catalog + messaging)."""

from __future__ import annotations

import httpx
import pytest

from order_service.api.main import create_app
from order_service.application.ports import ProductInfo
from order_service.config import Settings
from tests.conftest import TEST_DATABASE_URL
from tests.unit.fakes import FakeCatalogClient, RecordingPublisher


@pytest.fixture
async def client(engine):
    settings = Settings(database_url=TEST_DATABASE_URL)
    publisher = RecordingPublisher()
    catalog = FakeCatalogClient({"p1": ProductInfo("p1", "Widget", 1000)})
    app = create_app(settings, publisher=publisher, catalog_client=catalog)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await app.state.engine.dispose()


async def test_create_and_get_order(client):
    create = await client.post(
        "/api/orders",
        json={"user_id": "u1", "items": [{"product_id": "p1", "quantity": 2}]},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["total_amount"] == 2000
    assert body["status"] == "reserving"

    got = await client.get(f"/api/orders/{body['id']}")
    assert got.status_code == 200
    assert got.json()["id"] == body["id"]


async def test_create_order_unknown_product_returns_404(client):
    response = await client.post(
        "/api/orders",
        json={"user_id": "u1", "items": [{"product_id": "missing", "quantity": 1}]},
    )
    assert response.status_code == 404


async def test_create_order_empty_items_returns_422(client):
    response = await client.post(
        "/api/orders",
        json={"user_id": "u1", "items": []},
    )
    assert response.status_code == 422


async def test_list_orders(client):
    await client.post(
        "/api/orders",
        json={"user_id": "u1", "items": [{"product_id": "p1", "quantity": 1}]},
    )
    listed = await client.get("/api/orders", params={"user_id": "u1"})
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1
