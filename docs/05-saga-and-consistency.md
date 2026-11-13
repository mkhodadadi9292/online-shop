# 05 — Saga, Compensation & Consistency

An order spans three services (Order, Inventory, Payment) and two databases. There
is no cross-service ACID transaction, so we need a **saga**: a sequence of local
transactions, each with a **compensating action** to undo it if a later step fails.

## Orchestration-based saga (used here)

The Order Service is the orchestrator — a state machine:

```
PENDING
  │ publish order.created
  ▼
RESERVING ── inventory.reservation_failed ──▶ CANCELLED
  │ publish inventory.reserved
  ▼
PAYING ── payment.failed ──▶ RELEASING ──▶ CANCELLED
  │ publish payment.completed
  ▼
CONFIRMED
```

Each transition is a **local DB write** (update order status) followed by a
**message publish**. The local write is the source of truth; the message is how
the next participant learns what to do.

## Compensation table

| Step | Action | Compensation |
|---|---|---|
| Reserve inventory | stock↓ reserved↑ | release (stock↑ reserved↓) |
| Process payment | money captured | refund |

If payment fails after inventory was reserved, the orchestrator emits
`inventory.released` to compensate.

## Consistency guarantees

- **Eventually consistent, never silently lost.** The saga guarantees the order
  reaches a terminal state (CONFIRMED or CANCELLED) with inventory and payment
  reconciled.
- **Idempotency:** every message carries `event_id`; consumers record processed
  ids and ignore duplicates. This makes redelivery safe.
- **At-least-once delivery** from the broker + idempotent consumers = effectively-once
  processing.

## Outbox pattern (recommended hardening)

A failure can occur between "commit DB" and "publish message". The **transactional
outbox** pattern fixes this: write the event into an `outbox` table in the *same*
DB transaction as the state change, then a relay publishes it. This guarantees the
message is emitted iff the transaction commits. (Documented here; implemented as a
simplified version where the publisher is called immediately after commit.)

## Why not 2PC?

Two-phase commit across services is brittle (locks held across network calls,
coordinator SPOF, poor availability). Sagas trade atomicity for availability and
are the standard choice for microservices.
