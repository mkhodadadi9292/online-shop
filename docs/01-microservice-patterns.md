# 01 — Microservice Patterns

## Why we split the shop into 5 services

| Service | Bounded context | Owns |
|---|---|---|
| User | identity & accounts | users, credentials, profiles |
| Catalog | product truth | products, categories, prices |
| Inventory | stock availability | stock, reserved quantity |
| Order | purchase intent & lifecycle | orders, order items, saga state |
| Payment | money movement | payments, refunds |

Each service owns **its own database** (database-per-service). Services never reach
into another service's tables; they interact only through the network (REST or
messages). This is the single most important property of the architecture: it
decouples teams, deployments, and scaling.

## Core patterns in use

- **Database per service** — no shared tables, so schema changes are local.
- **API gateway** — a single entry point (Traefik in K8s, Nginx locally) routes
  the frontend to the right service and terminates TLS.
- **Saga** — the order flow is a distributed transaction coordinated by the Order
  Service (see `05-saga-and-consistency.md`).
- **Event-driven integration** — Inventory and Payment react to events rather than
  being called in a fragile synchronous chain.
- **Idempotent consumers** — every event has an `event_id`; consumers dedupe so
  redelivery (at-least-once delivery) is safe.

## Pros and cons

**Pros**
- Independent deploy & scale (scale Inventory independently of Catalog).
- Fault isolation: a Payment bug does not take down product browsing.
- Technology freedom per service (though here we standardize on FastAPI for velocity).
- Clear ownership boundaries mirror the business.

**Cons**
- Operational complexity: more moving parts, more deployments, more logs.
- Distributed transactions are hard — hence the saga.
- Network latency & partial failure must be handled explicitly.
- Cross-service queries (e.g. "orders with product names") require composition.

## When this is (and isn't) worth it

- **Small scale / small team:** a modular monolith is usually cheaper. The split
  pays off once you have independent teams or uneven load.
- **This project** deliberately uses microservices as a learning vehicle, so the
  overhead is the point.
