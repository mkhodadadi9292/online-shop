# 06 — Race Conditions & Locking (limited stock)

The critical requirement: **two buyers must never oversell the last item.**

## The race

Two concurrent requests both read `stock = 1`, both believe they can buy, both
write `stock = 0`, and two orders are confirmed against one item.

## Layer 1 — Atomic conditional UPDATE (the correctness backbone)

Instead of read-then-write, the Inventory Service mutates in a single statement:

```sql
UPDATE inventory
SET stock = stock - :qty, reserved = reserved + :qty
WHERE product_id = :pid AND stock >= :qty
RETURNING stock;
```

- The `WHERE stock >= :qty` guard runs **atomically** under the row lock.
- If `0` rows are returned → reject with `InsufficientStock`.
- This is correct under any concurrency without application-level locks, because
  Postgres serializes the two updates on the row.

This is the primary defense and passes the concurrency test (N parallel reserves,
assert total reserved ≤ initial stock).

## Layer 2 — Redis distributed lock (cross-service critical section)

Used to serialize the reserve/release **around** the DB operation when the flow
spans services (or when we need to coordinate with a cache):

```
SET lock:inventory:{pid} <owner> NX PX 5000
```

- `NX` = only acquire if absent; `PX 5000` = TTL so a crashed holder can't deadlock.
- Owner token + Lua-script release prevents releasing someone else's lock.
- Held only for the short critical section (never across the whole saga).

**Trade-off:** adds a dependency and TTL/expiry edge cases, which is why the atomic
UPDATE remains the source of truth even when the lock is used.

## Layer 3 — Idempotency

Broker redelivery could run "reserve" twice for the same order. Consumers dedupe on
`event_id` so a duplicate message is a no-op. Without this, a redelivered
`order.created` would double-reserve.

## Why not just `SELECT ... FOR UPDATE`?

`SELECT ... FOR UPDATE` (pessimistic row lock) also works and is simpler to reason
about, but the conditional UPDATE is lock-free from the app's perspective, shorter,
and less prone to deadlock in high contention. Both are valid; we chose the
conditional UPDATE as primary.
