# Frontier Tribe OS

> Operations platform for EVE Frontier Tribes and Syndicates — a toolkit for civilization.

**EVE Frontier x Sui Hackathon 2026** | March 11-31

## What It Does

Three integrated modules for tribe leaders:

- **Census** — Player authentication, member roster with roles, join request workflow
- **Forge Planner** — Production job board, tribe inventory, material gap analysis
- **Ledger** — Sui token treasury, member balances, transaction history

## Quick Start

```bash
# Full stack with Docker
cp .env.example .env
docker-compose up

# Or run separately:
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

Dev login: `POST http://localhost:8000/auth/dev-login?name=YourName`

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React + TypeScript + Tailwind CSS + Vite |
| Backend | FastAPI + SQLAlchemy (async) |
| Database | PostgreSQL |
| Cache | Redis |
| Auth | EVE Frontier SSO + JWT |
| Blockchain | Sui TypeScript SDK |

## License

MIT
