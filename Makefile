# --- Containers ---
up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev up -d

down:
	docker compose down

rebuild:
	docker compose build --no-cache

logs:
	docker compose logs -f api

# --- Backend quality gates (inside container) ---
fmt:
	docker compose exec api ruff format .
	docker compose exec api black .

lint:
	docker compose exec api ruff check .
	docker compose exec api mypy .

# --- DB migrations ---
migrate:
	docker compose exec api alembic upgrade head

makemigration:
	docker compose exec api alembic revision --autogenerate -m "update"

# --- Frontend ---
fe-dev:
	cd frontend/vue-app && npm run dev

fe-build:
	cd frontend/vue-app && npm run build

# --- Utilities ---
redis-ping:
	docker compose exec redis redis-cli ping

ps:
	docker compose ps
