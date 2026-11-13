"""Full cross-service saga e2e tests.

Runs the real RabbitMQ/Postgres/Redis infrastructure (started by docker compose)
with in-process FastAPI apps, exercising the complete saga:

    order.created -> inventory.reserve -> inventory.reserved
        -> payment.requested -> payment.completed -> order.confirmed

plus the oversell (race condition) and payment-failure (compensation) paths.
"""

from __future__ import annotations

import asyncio
import time

import httpx
import pytest

from catalog_service.api.main import create_app as catalog_app
from catalog_service.config import Settings as CatalogSettings
from catalog_service.infrastructure.db import Base as CatalogBase
from inventory_service.api.main import create_app as inventory_app
from inventory_service.config import Settings as InventorySettings
from inventory_service.infrastructure.consumer import InventoryConsumer
from inventory_service.infrastructure.db import Base as InventoryBase
from order_service.api.main import create_app as order_app
from order_service.application.ports import ProductInfo
from order_service.config import Settings as OrderSettings
from order_service.infrastructure.consumer import OrderSagaConsumer
from order_service.infrastructure.db import Base as OrderBase
from order_service.infrastructure.publisher import RabbitMQEventPublisher
from payment_service.api.main import create_app as payment_app
from payment_service.config import Settings as PaymentSettings
from payment_service.infrastructure.consumer import PaymentConsumer
from payment_service.infrastructure.db import Base as PaymentBase
from payment_service.infrastructure.gateway import MockPaymentGateway

RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"
EXCHANGE = "shop.events"
DECLINE_AMOUNT = 424242

DB = {
    "catalog": "postgresql+asyncpg://postgres:postgres@localhost:5432/catalog_db_test",
    "inventory": "postgresql+asyncpg://postgres:postgres@localhost:5432/inventory_db_test",
    "payment": "postgresql+asyncpg://postgres:postgres@localhost:5432/payments_db_test",
    "order": "postgresql+asyncpg://postgres:postgres@localhost:5432/orders_db_test",
}


class _FakeCatalog:
    async def get_product(self, product_id: str) -> ProductInfo | None:
        if product_id == "decline":
            return ProductInfo("decline", "Declining item", DECLINE_AMOUNT)
        return ProductInfo(product_id, "Product", 1000)


async def _reset(engine, base) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.drop_all)
        await conn.run_sync(base.metadata.create_all)


async def _wait_for_status(client: httpx.AsyncClient, order_id: str, targets: set[str], timeout: float = 15.0) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = await client.get(f"/api/orders/{order_id}")
        status = response.json()["status"]
        if status in targets:
            return status
        await asyncio.sleep(0.1)
    raise TimeoutError(f"order {order_id} did not reach {targets}")


async def _wait_for_stock(client: httpx.AsyncClient, product_id: str, expected: int, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = await client.get(f"/api/inventory/{product_id}")
        if response.json()["stock"] == expected:
            return
        await asyncio.sleep(0.1)
    raise TimeoutError(f"inventory {product_id} did not reach stock {expected}")


@pytest.fixture
async def stack():
    # Build the four services used by the saga (user service not needed here).
    order_settings = OrderSettings(database_url=DB["order"])
    inventory_settings = InventorySettings(database_url=DB["inventory"])
    payment_settings = PaymentSettings(database_url=DB["payment"], decline_amount=DECLINE_AMOUNT)
    catalog_settings = CatalogSettings(database_url=DB["catalog"])

    publisher = RabbitMQEventPublisher(RABBITMQ_URL, EXCHANGE)
    gateway = MockPaymentGateway(decline_amount=DECLINE_AMOUNT)

    order = order_app(order_settings, publisher=publisher, catalog_client=_FakeCatalog())
    inventory = inventory_app(inventory_settings, lock=None)
    payment = payment_app(payment_settings, gateway=gateway)
    catalog = catalog_app(catalog_settings)

    await _reset(order.state.engine, OrderBase)
    await _reset(inventory.state.engine, InventoryBase)
    await _reset(payment.state.engine, PaymentBase)
    await _reset(catalog.state.engine, CatalogBase)

    await publisher.connect()

    order_consumer = OrderSagaConsumer(RABBITMQ_URL, EXCHANGE, order.state.session_factory, publisher)
    inventory_consumer = InventoryConsumer(RABBITMQ_URL, EXCHANGE, inventory.state.session_factory)
    payment_consumer = PaymentConsumer(RABBITMQ_URL, EXCHANGE, payment.state.session_factory, gateway)
    await order_consumer.start()
    await inventory_consumer.start()
    await payment_consumer.start()

    async def client(app):
        transport = httpx.ASGITransport(app=app)
        return httpx.AsyncClient(transport=transport, base_url="http://test")

    order_client = await client(order)
    inventory_client = await client(inventory)

    yield {"order": order_client, "inventory": inventory_client}

    await order_client.aclose()
    await inventory_client.aclose()
    await order_consumer.stop()
    await inventory_consumer.stop()
    await payment_consumer.stop()
    await publisher.close()
    await order.state.engine.dispose()
    await inventory.state.engine.dispose()
    await payment.state.engine.dispose()
    await catalog.state.engine.dispose()


async def test_happy_path_confirms_and_decrements_stock(stack):
    await stack["inventory"].post("/api/inventory", json={"product_id": "p1", "stock": 10})

    created = await stack["order"].post(
        "/api/orders",
        json={"user_id": "u1", "items": [{"product_id": "p1", "quantity": 2}]},
    )
    assert created.status_code == 201
    order_id = created.json()["id"]

    status = await _wait_for_status(stack["order"], order_id, {"confirmed", "cancelled"})
    assert status == "confirmed"

    stock = await stack["inventory"].get("/api/inventory/p1")
    assert stock.json()["stock"] == 8


async def test_oversell_limited_stock_no_oversell(stack):
    await stack["inventory"].post("/api/inventory", json={"product_id": "hot", "stock": 5})

    async def place() -> str:
        response = await stack["order"].post(
            "/api/orders",
            json={"user_id": "u", "items": [{"product_id": "hot", "quantity": 1}]},
        )
        return response.json()["id"]

    order_ids = await asyncio.gather(*[place() for _ in range(12)])

    statuses = await asyncio.gather(
        *[_wait_for_status(stack["order"], oid, {"confirmed", "cancelled"}) for oid in order_ids]
    )
    assert statuses.count("confirmed") == 5
    assert statuses.count("cancelled") == 7

    stock = await stack["inventory"].get("/api/inventory/hot")
    assert stock.json()["stock"] == 0


async def test_payment_failure_releases_stock(stack):
    await stack["inventory"].post("/api/inventory", json={"product_id": "decline", "stock": 3})

    created = await stack["order"].post(
        "/api/orders",
        json={"user_id": "u1", "items": [{"product_id": "decline", "quantity": 1}]},
    )
    order_id = created.json()["id"]

    status = await _wait_for_status(stack["order"], order_id, {"confirmed", "cancelled"})
    assert status == "cancelled"

    await _wait_for_stock(stack["inventory"], "decline", 3)
