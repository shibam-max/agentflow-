.PHONY: up down build test migrate logs clean

## Start all services locally
up:
	docker compose up --build -d
	@echo "\nServices running:"
	@echo "  Frontend:      http://localhost:3000"
	@echo "  API Gateway:   http://localhost:8080"
	@echo "  Orchestrator:  http://localhost:8000/docs"

## Stop all services
down:
	docker compose down

## Run DB migrations
migrate:
	docker compose exec orchestrator python -m alembic upgrade head

## Run all tests
test:
	@echo "--- Java tests ---"
	cd apps/api-gateway && mvn test -B
	@echo "--- Python tests ---"
	cd apps/orchestrator && pytest tests/ -v
	@echo "--- TypeScript tests ---"
	cd apps/frontend && npm test

## Tail logs from all services
logs:
	docker compose logs -f

## Validate Terraform
tf-validate:
	cd infra/terraform && terraform init -backend=false && terraform validate

## Clean build artifacts
clean:
	cd apps/api-gateway && mvn clean
	find apps/orchestrator -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	cd apps/frontend && rm -rf .next node_modules
