# 03 — Bottlenecks & Scaling (Small / Medium / High)

Assumption: deployment is **Kubernetes** at high scale.

## Small scale (1 instance per service, single node)

- **Bottleneck:** the database. A single Postgres with 5 databases is fine, but it
  is the first thing to saturate.
- **Mitigations:** connection pooling (pgbouncer / asyncpg pool), indexes on hot
  queries, cache catalog reads.

## Medium scale (few replicas, read-heavy)

- **Bottleneck:** synchronous call chains and the DB read path.
- **Mitigations:**
  - Scale stateless services horizontally (more replicas behind a Service).
  - Add **Redis cache** in front of Catalog reads (product lists, details).
  - Move the write path to async messaging so a slow Inventory doesn't block Orders.
  - Read replicas for Catalog (read-heavy) once write volume is low.

## High scale (many replicas, multi-node, K8s)

- **Bottlenecks and their fixes:**

| Bottleneck | Fix |
|---|---|
| Single Postgres writer | sharding by tenant/product; read replicas; managed DB with autoscaling |
| Hot rows in Inventory (popular product) | atomic conditional UPDATE (lock-free path) + Redis distributed lock only around the critical section; consider caching stock with a fast decrement (Redis `DECRBY` + reconciliation job) |
| RabbitMQ broker saturation | cluster RabbitMQ, shard queues, tune prefetch, monitor queue depth as an autoscaling signal |
| API gateway as SPOF | replicate gateway, L7 load balancing via Ingress controller |
| Connection exhaustion | pgbouncer, bounded asyncpg pool, connection-per-replica budget |
| Sync call latency | keep only reads synchronous; everything on the write path is event-driven |
| Observability gap | distributed tracing (OpenTelemetry) keyed on `correlation_id` |

## Horizontal scaling rules

- **Stateless services** (User, Catalog, Order, Payment, Inventory) scale by adding
  replicas; keep all state in the DB/Redis/RabbitMQ.
- **Stateful services** (Postgres, RabbitMQ, Redis) scale via their own mechanisms
  (replication, clustering), not by adding random replicas.
- Use **HPA** on CPU + custom metrics (queue depth) — see `04-kubernetes-deployment.md`.

## The scaling philosophy

Push state to the edges (cache, broker, DB) and keep the application layer
stateless and disposable. The application layer should never be the bottleneck —
if it is, add replicas.
