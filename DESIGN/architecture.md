# Architecture

Online-shop microservices — a learning vehicle for system design and distributed-systems
patterns. Backend is Python/FastAPI, frontend is React/TypeScript.

## 1. System context

Five independently deployable services, each owning its own PostgreSQL database. The
frontend reads over synchronous REST and the write path flows through an asynchronous,
orchestration-based saga over RabbitMQ. Redis provides a distributed lock for the
inventory critical section.

```mermaid
flowchart LR
    U[User / Browser] --> FE[Frontend storefront\nReact + TS\n:8080]

    FE -->|REST reads + order writes| GW[Vite proxy /api/*]

    GW -->|"/api/users"| US[user-service\n:8000]
    GW -->|"/api/products"| CS[catalog-service\n:8001]
    GW -->|"/api/inventory"| IS[inventory-service\n:8002]
    GW -->|"/api/orders"| OS[order-service\n:8003]
    GW -->|"/api/payments"| PS[payment-service\n:8004]

    US --> UDB[(users_db)]
    CS --> CDB[(catalog_db)]
    IS --> IDB[(inventory_db)]
    OS --> ODB[(orders_db)]
    PS --> PDB[(payments_db)]

    OS -->|publish / consume| RMQ{{RabbitMQ}}
    IS --> RMQ
    PS --> RMQ
    IS --> RDS[(Redis lock)]
```

## 2. Communication model

**Hybrid:**

- **Synchronous REST** for reads: frontend → catalog / user / inventory / order reads.
- **Async RabbitMQ saga** for the write path (orchestration-based).

Event contracts are the single source of truth in
`backend/shared/src/shop_shared/events.py`. Every event carries a `correlation_id`
(ties it to one saga/order) and an `event_id` (idempotent consumption). Amounts are
integer minor units (cents).

| Direction | Protocol | Used for |
|---|---|---|
| frontend → services | REST (Vite proxy) | catalog, auth, order create, order read, payment read |
| order → catalog | REST (sync client) | price lookup at order creation |
| order → inventory → payment | RabbitMQ | saga orchestration |

## 3. Saga happy path

```mermaid
sequenceDiagram
    autonumber
    participant FE as Frontend
    participant OS as Order Service
    participant INV as Inventory Service
    participant PAY as Payment Service
    participant RMQ as RabbitMQ

    FE->>OS: POST /api/orders
    OS->>OS: create order (PENDING → RESERVING)
    OS->>OS: commit() before publish
    OS->>RMQ: publish order.created
    RMQ->>INV: order.created
    INV->>INV: atomic reserve (UPDATE ... WHERE stock >= qty)
    INV-->>INV: Redis lock around critical section
    INV->>RMQ: publish inventory.reserved
    RMQ->>OS: inventory.reserved
    OS->>OS: RESERVING → PAYING, commit()
    OS->>RMQ: publish payment.requested
    RMQ->>PAY: payment.requested
    PAY->>PAY: process payment
    PAY->>RMQ: publish payment.completed
    RMQ->>OS: payment.completed
    OS->>OS: PAYING → CONFIRMED, commit()
    OS->>RMQ: publish order.confirmed
```

## 4. Saga compensation (failure paths)

```mermaid
sequenceDiagram
    autonumber
    participant OS as Order Service
    participant INV as Inventory Service
    participant PAY as Payment Service
    participant RMQ as RabbitMQ

    Note over INV: insufficient stock
    INV->>RMQ: publish inventory.reservation_failed
    RMQ->>OS: inventory.reservation_failed
    OS->>OS: RESERVING → CANCELLED
    OS->>RMQ: publish order.cancelled

    Note over PAY: payment declined
    PAY->>RMQ: publish payment.failed
    RMQ->>OS: payment.failed
    OS->>OS: PAYING → CANCELLED
    OS->>RMQ: publish inventory.released (compensation)
    RMQ->>INV: inventory.released
    INV->>INV: release reserved stock
    OS->>RMQ: publish order.cancelled
```

## 5. Order state machine

The Order Service is the saga orchestrator.

```mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> RESERVING: create_order()
    RESERVING --> PAYING: inventory.reserved
    RESERVING --> CANCELLED: inventory.reservation_failed
    PAYING --> CONFIRMED: payment.completed
    PAYING --> CANCELLED: payment.failed\n(+ inventory.released)
    CANCELLED --> [*]
    CONFIRMED --> [*]
```

## 6. Service internal layout (lite-DDD)

Every service follows the same shape under `backend/services/<svc>/src/<pkg>/`.

```mermaid
flowchart TB
    subgraph SVC["Service package"]
        API[api/ - FastAPI routers, pydantic schemas, deps, main]
        APP[application/ - use cases + Protocol ports]
        DOM[domain/ - pure entities + value objects]
        INF[infrastructure/ - SQLAlchemy, RabbitMQ, Redis, HTTP clients]
    end

    API --> APP
    APP --> DOM
    APP -->|implements Protocol ports| INF
    INF --> DB[(database)]
    INF --> RMQ{{RabbitMQ}}
    INF --> RDS[(Redis)]
```

Conventions:

- Application depends on `Protocol` ports; infrastructure implements them. Unit tests
  substitute in-memory fakes (`tests/unit/fakes.py`).
- `create_app(settings, ...)` is the app factory; `app.state` holds the engine, session
  factory, and injectable collaborators.
- The `get_session` dependency **commits after the request** — repositories only
  `flush()` writes, and the request-scoped session commits on success.
- Saga handlers **commit before publishing** the next event (a simplification of the
  transactional outbox pattern) so the orchestrator never reads stale state.

## 7. Concurrency & safety

- **Race-condition safety (limited stock):** inventory repository uses an atomic
  conditional `UPDATE ... WHERE stock >= qty RETURNING` — never read-then-write.
- **Distributed lock:** Redis lock wraps the inventory critical section.
- **Idempotency:** consumers dedupe on `event_id`; saga handlers also guard on the
  order's current status as defense in depth.

## 8. Deployment

Local full stack via Docker Compose (`cd backend && docker compose up --build`):

```mermaid
flowchart LR
    subgraph Infra
        PG[(postgres:16\n:5432)]
        RMQ{{rabbitmq:3-mgmt\n:5672 / :15672}}
        RDS[(redis:7\n:6379)]
    end

    subgraph Services
        US[user-service]
        CS[catalog-service]
        IS[inventory-service]
        OS[order-service]
        PS[payment-service]
    end

    FE[frontend nginx\n:8080]

    US --> PG
    CS --> PG
    IS --> PG
    OS --> PG
    PS --> PG
    IS --> RMQ
    IS --> RDS
    OS --> RMQ
    PS --> RMQ
    FE --> US
    FE --> CS
    FE --> IS
    FE --> OS
    FE --> PS
```

Kubernetes manifests live in `k8s/`. Per-service `Dockerfile`s live under
`backend/services/<svc>/Dockerfile`; the frontend Dockerfile is in
`frontend/storefront/`.

## 9. Ports

| Component | Port |
|---|---|
| user-service | 8000 |
| catalog-service | 8001 |
| inventory-service | 8002 |
| order-service | 8003 |
| payment-service | 8004 |
| frontend | 8080 |
| Postgres | 5432 |
| RabbitMQ (AMQP / mgmt) | 5672 / 15672 |
| Redis | 6379 |
