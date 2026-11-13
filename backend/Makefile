.PHONY: infra-up infra-down test-user test-catalog test-inventory test-payment test-order test-all

infra-up:
	docker compose up -d postgres rabbitmq redis

infra-down:
	docker compose down

test-user:
	cd services/user-service && pytest

test-catalog:
	cd services/catalog-service && pytest

test-inventory:
	cd services/inventory-service && pytest

test-payment:
	cd services/payment-service && pytest

test-order:
	cd services/order-service && pytest

test-all: test-user test-catalog test-inventory test-payment test-order
