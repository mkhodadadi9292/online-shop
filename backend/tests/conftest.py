"""Makes every service's src importable for the cross-service e2e suite."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

for service in (
    "user-service",
    "catalog-service",
    "inventory-service",
    "payment-service",
    "order-service",
):
    src = BACKEND / "services" / service / "src"
    if src.exists():
        sys.path.insert(0, str(src))

sys.path.insert(0, str(BACKEND / "shared" / "src"))
