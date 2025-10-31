# LostFits

Mono-repo for **LostFits** — an EVE Online killmail aggregation and analysis app focused on the *fits that were lost*.

- Frontend: **Vue 3 + TypeScript + Vite + Tailwind + vue-query**
- Backend: **FastAPI + SQLAlchemy + Alembic + RQ + APScheduler + httpx + tenacity**
- Infra: **DigitalOcean** (Droplet + Managed Postgres + Managed Redis + Spaces) with **Terraform** IaC
- Reverse proxy: **Caddy** (TLS via Let's Encrypt, HTTP/3)

## Quick Start (Local Dev)

1. **Install** Docker Desktop and `uv` (Python package manager):
   ```bash
   pipx install uv  # or: pip install uv
   ```

2. **Backend** env:
   ```bash
   cp services/api/.env.example services/api/.env
   ```

3. **Start** local stack:
   ```bash
   docker compose up -d --build
   ```

4. **Open**:
   - API docs: http://localhost:8000/docs
   - Health: http://localhost:8000/healthz
   - RQ Dashboard: http://localhost:9181
   - Frontend (dev server): see `frontend/README.md` (or serve built files with Caddy container)

## Terraform (DigitalOcean)

See `infra/README.md` for full instructions. This will create:
- VPC, Droplet (Docker Compose host), firewall
- Managed Postgres, Managed Redis
- Spaces bucket (for nightly pg_dump)
- DNS A record for **lostfits.com** → Droplet

> ⚠️ Provide a DigitalOcean API token and your Spaces access/secret keys as TF variables or environment variables.

## Deploy (high-level)

- Build images via GitHub Actions → push to GHCR
- SSH to Droplet from Action → `docker compose pull && docker compose up -d`
- Rsync frontend `dist/` to Droplet; Caddy serves it and reverse-proxies `/api/*`

See `.github/workflows/` for starter pipelines.
