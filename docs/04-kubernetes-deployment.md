# 04 — Kubernetes Deployment (high scale)

Each service ships as a `Deployment` (stateless) behind a `Service`, exposed through
an `Ingress`. Configuration flows through `ConfigMap`/`Secret`; scaling through HPA.

## Object map per service

```
Deployment  user-service        → Service user-service        (ClusterIP)
Deployment  catalog-service     → Service catalog-service
Deployment  inventory-service   → Service inventory-service
Deployment  order-service       → Service order-service
Deployment  payment-service     → Service payment-service
Ingress     shop                 → routes /api/users, /api/products, ... by path
StatefulSet postgres / rabbitmq / redis (or managed equivalents)
```

## Key practices encoded in `k8s/`

- **Readiness & liveness probes** — readiness gates traffic (service is ready to
  serve), liveness restarts wedged pods. Different endpoints for each.
- **Rolling updates** — `maxSurge`/`maxUnavailable` so deploys are zero-downtime.
- **HPA** — CPU-based autoscaling plus a custom metric on RabbitMQ queue depth so
  Order/Inventory scale with backlog, not just CPU.
- **ConfigMap** for non-secret config (DB host, exchange name); **Secret** for
  passwords and `JWT_SECRET`.
- **Resource requests/limits** — requests for scheduling, limits to stop noisy
  neighbors.
- **PodDisruptionBudget** — keep N replicas available during node drains.
- **Topology spread** — spread replicas across zones/nodes for availability.

## High-scale notes

- Prefer **managed Postgres/RabbitMQ/Redis** over in-cluster StatefulSets once
  operational burden matters; the K8s manifests document both.
- Use a **service mesh** or at least mTLS for inter-service traffic at scale.
- Centralized logging + metrics + tracing (OpenTelemetry) keyed on `correlation_id`.
- Gateway is horizontally scaled and fronted by the Ingress controller/LB.
