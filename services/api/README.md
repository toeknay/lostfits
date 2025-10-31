# LostFits

**LostFits** is a full-stack app that aggregates EVE Online killmail data to analyze and rank the most common ship fittings (that died, unfortunately).

---

## 🧱 Stack Overview

**Backend:** FastAPI (Python)  
**Task Queue:** Redis + RQ + APScheduler  
**Database:** PostgreSQL  
**Frontend:** Vue 3 + Vite  
**Reverse Proxy / Web Server:** Caddy  
**Containerization:** Docker + Docker Compose  
**Environment Profiles:** Dev / Prod overrides for flexible deployment

---

## 🚀 Local Development

### 1️⃣  Prerequisites
- Docker & Docker Compose installed  
- Node.js (for local Vue dev builds)  
- `uv` or `python3` installed if you want to run backend tests outside Docker

### 2️⃣  Environment Setup
Copy the example environment file for the API:

```bash
cp services/api/.env.example services/api/.env
```

### 3️⃣  Start the stack
Run with dev overrides (Caddy on port 8080, RQ Dashboard on 9181):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev up -d --build
```

Then open:

- **Frontend:** http://localhost:8080  
- **Backend API:** http://localhost:8000/docs  
- **RQ Dashboard:** http://localhost:9181  
- **Postgres:** localhost:5433  
- **Redis:** localhost:6380

Stop everything:

```bash
docker compose down
```

---

## 🗄️  Database Migrations

Generate and apply Alembic migrations:

```bash
docker compose exec api alembic revision --autogenerate -m "init"
docker compose exec api alembic upgrade head
```

---

## 🧰 Frontend Workflow

You can develop the Vue frontend independently:

```bash
cd frontend/vue-app
npm install
npm run dev
```

That runs a local dev server on http://localhost:5173  
The production build is created with:

```bash
npm run build
```

Built files are served by Caddy from `frontend/vue-app/dist/`.

---

## ⚙️ Production Deployment

1. Point your domain’s **A record** to your Droplet / server.  
2. Set your domain in an environment variable:
   ```bash
   export DOMAIN=lostfits.com
   ```
3. Launch the production stack:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

Caddy will automatically fetch HTTPS certificates for `$DOMAIN`.

---

## 🧩 File Overview

| File | Purpose |
|------|----------|
| `docker-compose.yml` | Base stack definition (common services) |
| `docker-compose.dev.yml` | Dev override (8080 ports, RQ dashboard, local DB/Redis ports) |
| `docker-compose.prod.yml` | Prod override (real TLS, no RQ dashboard exposure) |
| `Caddyfile.dev` | Local HTTP config (auto_https off) |
| `Caddyfile.prod` | Production HTTPS config for `$DOMAIN` |
| `services/api/` | FastAPI app, background jobs, scheduler |
| `frontend/vue-app/` | Vue 3 frontend built with Vite |

---

## 💡 Useful Commands

| Action | Command |
|---------|----------|
| See logs | `docker compose logs -f api` |
| Tail worker logs | `docker compose logs -f worker` |
| Open a shell in the API container | `docker compose exec api bash` |
| Check Redis health | `docker compose exec redis redis-cli ping` |
| Rebuild everything | `docker compose build --no-cache` |
| Clean everything | `docker compose down -v` |

---

## 🧠 Notes

- For dev, all services are on Docker’s internal network (`redis://redis:6379/0`, `postgres://lostfits:lostfits@db:5432/lostfits`).
- Don’t install Redis or Postgres locally; Docker handles them.
- The `rq-dashboard` is dev-only and runs only with the `dev` profile.
- Caddy auto-redirects `/api/*` to the FastAPI backend.
- In prod, Caddy automatically manages TLS certificates via Let’s Encrypt.

---

## 🏁 Quick Start Summary

| Mode | Command | URL |
|------|----------|-----|
| **Dev** | `docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev up -d` | http://localhost:8080 |
| **Prod** | `export DOMAIN=lostfits.com && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` | https://lostfits.com |

---