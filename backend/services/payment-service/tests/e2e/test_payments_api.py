"""End-to-end HTTP tests for the payments API."""

from __future__ import annotations

import httpx
import pytest

from payment_service.api.main import create_app
from payment_service.config import Settings
from payment_service.infrastructure.gateway import MockPaymentGateway
from tests.conftest import TEST_DATABASE_URL


@pytest.fixture
async def client(engine):
    settings = Settings(database_url=TEST_DATABASE_URL)
    app = create_app(settings, gateway=MockPaymentGateway())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await app.state.engine.dispose()


async def test_process_and_get_payment(client):
    process = await client.post("/api/payments", json={"order_id": "o1", "amount": 1000})
    assert process.status_code == 201
    body = process.json()
    assert body["status"] == "completed"

    got = await client.get(f"/api/payments/{body['id']}")
    assert got.status_code == 200
    assert got.json()["order_id"] == "o1"


async def test_refund_payment(client):
    process = await client.post("/api/payments", json={"order_id": "o1", "amount": 1000})
    payment_id = process.json()["id"]
    refund = await client.post(f"/api/payments/{payment_id}/refund")
    assert refund.status_code == 200
    assert refund.json()["status"] == "refunded"


async def test_get_missing_returns_404(client):
    assert (await client.get("/api/payments/missing")).status_code == 404
