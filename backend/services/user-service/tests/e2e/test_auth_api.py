"""End-to-end HTTP tests for the auth API (real Postgres, in-process ASGI)."""

from __future__ import annotations

import httpx
import pytest

from user_service.api.main import create_app
from user_service.config import Settings
from tests.conftest import TEST_DATABASE_URL


@pytest.fixture
async def client(engine):
    settings = Settings(database_url=TEST_DATABASE_URL, jwt_secret="test-secret")
    app = create_app(settings)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await app.state.engine.dispose()


async def test_register_login_me_flow(client):
    register = await client.post(
        "/api/users/auth/register",
        json={"email": "foo@bar.com", "password": "password123", "full_name": "Foo"},
    )
    assert register.status_code == 201
    body = register.json()
    assert body["email"] == "foo@bar.com"

    login = await client.post(
        "/api/users/auth/login",
        json={"email": "foo@bar.com", "password": "password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token

    me = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["id"] == body["id"]


async def test_register_duplicate_returns_409(client):
    payload = {"email": "dup@bar.com", "password": "password123"}
    assert (await client.post("/api/users/auth/register", json=payload)).status_code == 201
    second = await client.post("/api/users/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["code"] == "conflict"


async def test_login_wrong_password_returns_401(client):
    await client.post(
        "/api/users/auth/register",
        json={"email": "foo@bar.com", "password": "password123"},
    )
    login = await client.post(
        "/api/users/auth/login",
        json={"email": "foo@bar.com", "password": "wrong-password"},
    )
    assert login.status_code == 401


async def test_me_without_token_returns_401(client):
    response = await client.get("/api/users/me")
    assert response.status_code == 401


async def test_register_invalid_email_returns_422(client):
    response = await client.post(
        "/api/users/auth/register",
        json={"email": "not-an-email", "password": "password123"},
    )
    assert response.status_code == 422
