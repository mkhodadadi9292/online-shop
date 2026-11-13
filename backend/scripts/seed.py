"""Seed the catalog + inventory with sample data for local development.

Run after the services are up (e.g. `docker compose up` or the run.py servers).
"""

from __future__ import annotations

import httpx

CATALOG = "http://localhost:8001"
INVENTORY = "http://localhost:8002"

PRODUCTS = [
    {
        "name": "Wireless Headphones",
        "description": "Over-ear noise-cancelling headphones with 30h battery.",
        "price": 8999,
        "category": "electronics",
    },
    {
        "name": "Mechanical Keyboard",
        "description": "Hot-swappable 75% keyboard with tactile switches.",
        "price": 12999,
        "category": "electronics",
    },
    {
        "name": "Cotton T-Shirt",
        "description": "Everyday heavyweight cotton tee.",
        "price": 2499,
        "category": "apparel",
    },
    {
        "name": "Ceramic Mug",
        "description": "12oz matte ceramic mug.",
        "price": 1899,
        "category": "home",
    },
    {
        "name": "Desk Lamp",
        "description": "Dimmable LED desk lamp with USB-C charging.",
        "price": 4499,
        "category": "home",
    },
    {
        "name": "Field Notes Notebook",
        "description": "3-pack of pocket notebooks.",
        "price": 1299,
        "category": "books",
    },
]


def main() -> None:
    for product in PRODUCTS:
        response = httpx.post(f"{CATALOG}/api/products", json=product)
        response.raise_for_status()
        product_id = response.json()["id"]
        stock = httpx.post(
            f"{INVENTORY}/api/inventory",
            json={"product_id": product_id, "stock": 100},
        )
        stock.raise_for_status()
        print(f"seeded {product['name']} ({product_id})")


if __name__ == "__main__":
    main()
