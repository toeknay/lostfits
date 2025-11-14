# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**LostFits** is an EVE Online killmail aggregation and analysis app that tracks and ranks the most common ship fittings that were destroyed. It's a monorepo with:
- **Frontend**: Vue 3 + TypeScript + Vite + Tailwind + vue-query
- **Backend**: FastAPI + SQLAlchemy + Alembic + RQ + APScheduler + httpx + tenacity
- **Infrastructure**: DigitalOcean (Droplet + Managed Postgres + Managed Redis + Spaces) with Terraform IaC
- **Reverse Proxy**: Caddy (TLS via Let's Encrypt, HTTP/3)

## Development Commands

### Docker Compose Stack

**Start local dev environment:**
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev up -d --build
# Or use the Makefile:
make up
```

**Stop services:**
```bash
docker compose down
# Or:
make down
```

**View API logs:**
```bash
docker compose logs -f api
# Or:
make logs
```

**Rebuild from scratch:**
```bash
docker compose build --no-cache
# Or:
make rebuild
```

### Backend (FastAPI)

**Code formatting:**
```bash
docker compose exec api ruff format .
docker compose exec api black .
# Or:
make fmt
```

**Linting & type checking:**
```bash
docker compose exec api ruff check .
docker compose exec api mypy .
# Or:
make lint
```

**Database migrations:**
```bash
# Generate migration from model changes:
docker compose exec api alembic revision --autogenerate -m "description"
# Or:
make makemigration

# Apply migrations:
docker compose exec api alembic upgrade head
# Or:
make migrate
```

**Run tests:**
```bash
docker compose exec api pytest
```

### Frontend (Vue 3)

**Development server (standalone):**
```bash
cd frontend/vue-app
npm install
npm run dev
# Or from root:
make fe-dev
```

**Build for production:**
```bash
cd frontend/vue-app
npm run build
# Or from root:
make fe-build
```

The production build outputs to `frontend/vue-app/dist/` which is served by Caddy.

### Local Access URLs

When running the dev stack:
- **Frontend (via Caddy)**: http://localhost:8080
- **Backend API docs**: http://localhost:8000/docs
- **Backend health**: http://localhost:8000/healthz
- **RQ Dashboard**: http://localhost:9181
- **Postgres**: localhost:5433
- **Redis**: localhost:6380

## Architecture

### Backend Structure

The backend follows a task-queue pattern with these key components:

- **API service** (`services/api/app/main.py`): FastAPI application serving REST endpoints
- **Worker service**: RQ worker that processes background jobs from Redis queue
- **Scheduler service** (`services/api/app/scheduler.py`): APScheduler instance that enqueues periodic tasks

**Directory layout:**
```
services/api/app/
├── main.py           # FastAPI application entry point
├── config.py         # Pydantic settings (env vars, ESI config, etc.)
├── db.py             # SQLAlchemy session management
├── scheduler.py      # APScheduler daemon for periodic tasks
├── models/           # SQLAlchemy ORM models
│   ├── fit.py
│   ├── killmail_raw.py
│   ├── item_type.py
│   └── fit_aggregate_daily.py
├── routes/           # FastAPI route handlers
│   ├── health.py
│   └── example.py
└── tasks/            # RQ background tasks
    └── ingest.py     # Task enqueuing and processing
```

**Key patterns:**
- Configuration is managed via `app/config.py` using `pydantic-settings` (loads from `.env`)
- ESI (EVE Swagger Interface) integration configured with rate limiting (`esi_max_qps`)
- Redis queue tasks are enqueued from scheduler or API endpoints and processed by RQ workers
- All services share the same Docker image built from `services/api/Dockerfile`

### Frontend Structure

Vue 3 SPA with minimal structure:
```
frontend/vue-app/src/
├── main.ts           # App entry point
├── App.vue           # Root component
├── router.ts         # Vue Router configuration
└── views/            # Page components
```

Uses `@tanstack/vue-query` for server state management and Axios for HTTP requests.

### Docker Compose Architecture

Three-layer compose setup:
1. **Base** (`docker-compose.yml`): Core service definitions (api, worker, scheduler, db, redis, caddy, rq-dashboard)
2. **Dev override** (`docker-compose.dev.yml`): Exposes ports for local access, enables RQ dashboard via `--profile dev`
3. **Prod override** (`docker-compose.prod.yml`): Production configuration with real TLS

**Service communication:**
- All services communicate via Docker internal networking (e.g., `redis://redis:6379/0`, `postgres://lostfits:lostfits@db:5432/lostfits`)
- Caddy reverse proxies `/api/*` to the FastAPI backend
- Frontend static files are served from `frontend/vue-app/dist/` by Caddy

### Database

PostgreSQL 16 with Alembic for migrations. Models use SQLAlchemy 2.0+ syntax. Migration files are in `services/api/alembic/versions/`.

## Data Pipeline

### Automated Jobs (Scheduler)

The scheduler service (`app/scheduler.py`) runs two periodic jobs:

1. **Killmail Fetching** - Every 10 seconds
   - Fetches new killmails from zKillboard RedisQ
   - Parses ship fittings and calculates fit signatures
   - Stores in `killmail_raw` and `fit` tables

2. **Item Type Seeding** - Daily at 03:00 UTC
   - Scans all killmails for unknown item types
   - Queues ESI fetch jobs for missing ships/modules/drones
   - Automatically discovers new items as killmails arrive

### Item Type Strategy

Currently uses **incremental seeding**: only fetches item types (ships, modules) that appear in ingested killmails (~700 items from ~100 killmails).

For production, consider pre-loading all ~12k EVE items from ESI using:
```bash
curl -X POST http://localhost:8000/api/admin/seed-types
```

This will take ~4-5 hours due to ESI rate limiting (3 QPS).

## Code Quality

The project uses pre-commit hooks configured in `.pre-commit-config.yaml`:
- **ruff**: Fast Python linter (replaces flake8, isort)
- **black**: Code formatter
- **mypy**: Static type checker

Settings are in `pyproject.toml` with line length set to 100 characters. Mypy excludes `alembic/` directory.

## Infrastructure

Terraform configuration in `infra/` provisions:
- VPC, Droplet, and firewall rules
- Managed PostgreSQL and Redis instances
- Spaces bucket for nightly pg_dump backups
- DNS A record pointing to Droplet

See `infra/README.md` for deployment instructions. Requires `DIGITALOCEAN_TOKEN` environment variable.

## Production Deployment

1. Terraform provisions infrastructure
2. GitHub Actions builds Docker images and pushes to GHCR
3. Action SSHs to Droplet and runs `docker compose pull && docker compose up -d`
4. Frontend `dist/` is rsynced to Droplet for Caddy to serve

See `.github/workflows/` for CI/CD pipelines.

## Environment Variables

Backend requires `.env` file in `services/api/`:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string (defaults to `redis://redis:6379/0`)
- `ESI_USER_AGENT`: User agent for EVE ESI API calls
- `ESI_MAX_QPS`: Rate limit for ESI requests
- `ZKILL_STREAM_URL`: (Optional) zKillboard websocket stream URL
- `SENTRY_DSN`: (Optional) Sentry error tracking

Copy from `services/api/.env.example` to get started.

## Testing

Run backend tests with:
```bash
docker compose exec api pytest
```

Tests are located in `services/api/tests/`.
