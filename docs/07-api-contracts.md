# 07 — API & Event Contracts

Single source of truth for the wire format. Implemented in `backend/shared/src/shop_shared/`
(`events.py` for messages; each service's `api/` for REST schemas).

## REST (synchronous, via gateway)

### User Service
| Method | Path | Description |
|---|---|---|
| POST | `/api/users/auth/register` | create account |
| POST | `/api/users/auth/login` | return JWT |
| GET | `/api/users/me` | current profile (auth) |

### Catalog Service
| Method | Path | Description |
|---|---|---|
| GET | `/api/products` | list w/ `search`, `category`, `min_price`, `max_price`, `sort`, `page`, `page_size` |
| GET | `/api/products/{id}` | product detail |
| POST/PUT/DELETE | `/api/products` | admin CRUD |

### Inventory Service
| Method | Path | Description |
|---|---|---|
| GET | `/api/inventory/{product_id}` | current stock/reserved |

### Order Service
| Method | Path | Description |
|---|---|---|
| POST | `/api/orders` | create order (auth) |
| GET | `/api/orders/{id}` | order status |
| GET | `/api/orders` | my orders (auth) |

### Payment Service
| Method | Path | Description |
|---|---|---|
| GET | `/api/payments/{id}` | payment status |

## Event contracts (asynchronous, RabbitMQ topic `shop.events`)

All events carry: `event_id` (idempotency), `correlation_id` (saga tracing),
`type`, `version`, `occurred_at`.

| Type | Producer | Consumer | Payload |
|---|---|---|---|
| `order.created` | Order | Inventory | order_id, user_id, items[], total_amount |
| `inventory.reserved` | Inventory | Order | order_id, items[] |
| `inventory.reservation_failed` | Inventory | Order | order_id, reason |
| `payment.requested` | Order | Payment | order_id, amount |
| `payment.completed` | Payment | Order | order_id, payment_id |
| `payment.failed` | Payment | Order | order_id, reason |
| `inventory.released` | Order | Inventory | order_id, items[] |
| `order.confirmed` / `order.cancelled` | Order | (observers) | order_id, reason? |

`items[]` = `{ product_id, quantity, unit_price }`. Money is integer **minor units**
(cents).
