# Frontier Tribe OS

## What This Is
Web-based operations platform for EVE Frontier Tribes and Syndicates. Hackathon submission for EVE Frontier x Sui Hackathon 2026 (March 11-31).

## Tech Stack
- **Backend**: FastAPI (Python 3.12), SQLAlchemy async, PostgreSQL, Redis, Alembic
- **Frontend**: React + TypeScript + Tailwind CSS v4 + Vite + React Router
- **Auth**: EVE Frontier SSO (TBD — may be wallet-based) + JWT + dev-login bypass
- **Blockchain**: Sui TypeScript SDK (Ledger module, Week 3)

## Modules (Build Order)
1. **Census** (Week 1) — Auth, member roster, roles, join requests
2. **Forge** (Week 2) — Production job board, inventory, gap analysis
3. **Ledger** (Week 3) — Sui token treasury, balances, transactions

## Key Rules
- Modules are independent — Ledger not being ready must not break Census
- Every route needs auth middleware — no unauthenticated access to tribe data
- All World API calls must have try/except + static data fallback
- Dev-login is enabled when ENVIRONMENT=development
- Never hardcode credentials

## Commands
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Docker (full stack)
docker-compose up
```

## Database
- Async PostgreSQL via asyncpg
- Auto-creates tables in dev mode (lifespan)
- Use Alembic for migrations in prod

## API Endpoints
- `POST /auth/dev-login?name=Pilot` — Dev-mode character login
- `GET /auth/login` — EVE Frontier SSO redirect
- `GET /auth/callback?code=...` — SSO callback
- `POST /census/tribes` — Create tribe
- `GET /census/tribes/{id}/members` — List roster
- `POST /census/tribes/join/{invite_code}` — Request to join
- `POST /census/tribes/{id}/requests/{id}` — Approve/deny
- `PATCH /census/tribes/{id}/members/{id}/role` — Change role
- `POST /forge/tribes/{id}/jobs` — Create production job
- `GET /forge/tribes/{id}/jobs` — List jobs (Kanban)
- `PATCH /forge/tribes/{id}/jobs/{id}` — Update job status
- `PUT /forge/tribes/{id}/inventory` — Upsert inventory item
- `GET /forge/tribes/{id}/inventory` — List inventory
