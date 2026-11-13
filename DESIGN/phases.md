# Implementation Phases — Status

Status legend: `planned` → `in progress` → `finish` (code written, tests not yet verified) → `done` (verified: tests pass).

| # | Phase | Status | Notes |
|---|---|---|---|
| 1 | Scaffold: repo layout, shared package, docker-compose infra, docs skeleton | done | `backend/shared`, `docs/01..07`, compose infra |
| 2 | User Service (TDD: domain, use cases, repos, API, JWT) | done | 12 unit + integration + e2e tests pass |
| 3 | Catalog Service (TDD: CRUD, search/filter/pagination) | done | 8 unit + integration + e2e tests pass |
| 4 | Inventory Service (TDD: atomic reserve/release + Redis lock + idempotency) | done | race-condition test (30 concurrent → 10 success) passes |
| 5 | Payment Service (TDD: process/refund, idempotency) | done | 6 unit + integration + e2e tests pass |
| 6 | Order Service + Saga orchestrator + RabbitMQ (TDD) | done | 11 unit + integration + e2e tests pass |
| 7 | Backend e2e tests (order flow, oversell, rollback) | done | full saga over real RabbitMQ: happy path, oversell, payment-failure compensation |
| 8 | Frontend storefront (React + TS + Tailwind) | done | builds, type-checks, unit tests pass; live smoke test through Vite proxy works |
| 9 | Frontend e2e tests (Playwright) | finish | `playwright.config.ts` + `e2e/shop.spec.ts` written (browser binaries not installed in this env) |
| 10 | Dockerfiles, full compose stack, K8s manifests, finalize docs | done | 5 service Dockerfiles + frontend Dockerfile, full compose, `k8s/` manifests, seed script |

## Verification summary
- Backend: 44 unit tests, per-service integration + e2e, and 3 cross-service saga e2e tests — all passing.
- Race condition verified: 30 concurrent reserves against 10 stock → exactly 10 succeed, no oversell.
- Full-stack smoke test: services + frontend + Vite proxy verified end-to-end (order `reserving → paying → confirmed`, stock decremented 100 → 98).
- `docs/` covers microservice patterns, communication, small/medium/high-scale bottlenecks, Kubernetes, saga/consistency, and race conditions.
