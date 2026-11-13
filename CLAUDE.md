# CLAUDE.md

Online-shop microservices built as a learning vehicle for system design and
distributed-systems patterns. Backend is Python/FastAPI; frontend is React/TS.

## Architecture

Five independently deployable services, each with **its own database**:

| Service | DB | Responsibility |
|---|---|---|
| `user-service` | `users_db` | register/login, JWT |
| `catalog-service` | `catalog_db` | products, categories, pricing |
| `inventory-service` | `inventory_db` | stock, reserve/release |
| `order-service` | `orders_db` | orders + **saga orchestrator** |
| `payment-service` | `payments_db` | payments, refunds |

**Communication (hybrid):**
- Synchronous REST for reads (frontend → catalog/user/inventory/order reads).
- Async RabbitMQ **orchestration-based saga** for the write path:
  `order.created → inventory.reserved → payment.requested → payment.completed → order.confirmed`,
  with `inventory.released` + `order.cancelled` compensation on failure.
- Order Service is the orchestrator (state machine `PENDING → RESERVING → PAYING → CONFIRMED | CANCELLED`).
- Event contracts live in `backend/shared/src/shop_shared/events.py`; amounts are integer minor units.

**Race-condition safety** (limited stock): the inventory repository uses an atomic
conditional `UPDATE ... WHERE stock >= qty RETURNING` — do not replace this with
read-then-write. A Redis distributed lock wraps the critical section; idempotent
consumers dedupe on `event_id`.

## Per-service code layout (lite-DDD)

Every service follows the same shape under `backend/services/<svc>/src/<pkg>/`:

```
domain/         pure entities + value objects (stdlib only)
application/    use cases + ports (Protocol interfaces for DI/testability)
infrastructure/ SQLAlchemy models/repos, RabbitMQ, Redis, HTTP clients
api/            FastAPI routers, pydantic schemas, deps, main (app factory)
run.py          production entrypoint (create tables, start consumer, uvicorn)
```

Conventions to preserve:
- Application depends on `Protocol` ports; infrastructure implements them. Unit
  tests substitute in-memory fakes (see `tests/unit/fakes.py`).
- `create_app(settings, ...)` is the app factory; `app.state` holds engine,
  session factory, and injectable collaborators.
- **The `get_session` dependency commits after the request** — writes only
  `flush()` in repositories, and the request-scoped session commits on success.
- **Saga handlers must `commit()` before publishing** the next event (see
  `order_service/application/saga.py`); otherwise the orchestrator can read stale
  state and stall. This is commit-before-publish, a simplification of the
  transactional outbox pattern (documented in `docs/05`).

## Testing

- Unit tests (`tests/unit`) need no infra. Integration + e2e need the Docker
  infra (Postgres/RabbitMQ/Redis) running with per-service `*_test` databases.
- Start infra: `cd backend && docker compose up -d postgres rabbitmq redis`
- Run a service's tests: `cd backend/services/<svc> && ../../.venv/bin/python -m pytest`
- Full cross-service saga e2e: `cd backend/tests && ../.venv/bin/python -m pytest`

Frontend (`frontend/storefront`): `npm run test` (Vitest), `npm run build`,
`npm run test:e2e` (Playwright — requires `npx playwright install` first).

## Running locally

- Backend deps are installed in `backend/.venv` (PyPI was flaky here — use
  `backend/install-deps.sh`, which installs via `uv` with retries).
- Full stack: `cd backend && docker compose up --build` (frontend on :8080).
- Or run services directly with `PORT=<port> PYTHONPATH=src .venv/bin/python -m <pkg>.run`,
  then `cd frontend/storefront && npm run dev` (Vite proxies `/api/*` to the services).
- Seed sample data: `backend/.venv/bin/python backend/scripts/seed.py`.

## Docs

`docs/01..07` cover microservice patterns, communication, small/medium/high-scale
bottlenecks, Kubernetes deployment, saga/consistency, and race conditions.
Phase tracking lives in `DESIGN/phases.md`.

## Notes

- This is not a git repository (no commits unless the user asks).
- `TASK_RECEIPT.md` is maintained per the global cost-receipt rule.
- Money is always integer minor units (cents) across service boundaries.
