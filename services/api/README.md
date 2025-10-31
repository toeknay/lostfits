# LostFits API

FastAPI backend with RQ (Redis Queue) and APScheduler.

## Local dev
Copy `.env.example` to `.env` and run from repo root:
```bash
docker compose up -d --build
```

Migrations:
```bash
docker compose exec api alembic revision --autogenerate -m "init"
docker compose exec api alembic upgrade head
```
