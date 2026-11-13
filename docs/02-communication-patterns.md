# 02 — Communication Patterns

This is the heart of the design. We use a **hybrid**: synchronous REST for reads,
asynchronous messaging for the write path.

## Synchronous (request/response) — REST over HTTP

Used for:
- Catalog queries (list / detail / search / filter)
- User auth (register / login)
- Inventory stock **read** (is this product in stock?)
- Order **read** (get my order status)

**When to use sync:** the caller needs an answer *now* to continue, the operation
is idempotent and fast, and the callee is expected to be up.

**Pros:** simple, debuggable, cacheable (HTTP caching), rich tooling.
**Cons:** tight temporal coupling — if the callee is down or slow, the caller
blocks/fails. Call chains multiply latency (order → inventory → payment = worst case).

## Asynchronous (event-driven) — RabbitMQ

Used for the order **write path**:

```
order.created ──▶ InventoryService.reserve
    ├── inventory.reserved ──▶ PaymentService.process
    │       ├── payment.completed ──▶ order.confirmed
    │       └── payment.failed ─────▶ inventory.released + order.cancelled
    └── inventory.reservation_failed ──▶ order.cancelled
```

**When to use async:** the operation has side effects across services, can be
eventually consistent, needs retries/compensation, or the producer shouldn't wait.

**Pros:** temporal decoupling (services can be down and catch up), natural retry
via broker redelivery, backpressure via queue length, fan-out.
**Cons:** eventual consistency (readers may see stale data), harder to trace/debug,
need idempotency because delivery is at-least-once.

## Messaging topology

- One **topic exchange** `shop.events`.
- Each service binds its own queue with routing keys it cares about
  (e.g. Inventory binds `order.created`; Payment binds `payment.requested`).
- `correlation_id` ties all events of one order together for tracing.

## Choosing between orchestration and choreography

- **Choreography:** each service only listens to events and reacts; no central brain.
  Very decoupled but the flow becomes implicit and hard to see.
- **Orchestration:** one service (Order) drives the flow explicitly as a state machine.
  Easier to reason about, test, and compensate.

We use **orchestration-based saga** (Order Service is the orchestrator), while still
transporting the messages over the broker — a pragmatic middle ground. See
`05-saga-and-consistency.md`.
