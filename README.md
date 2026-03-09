# Frontier Tribe OS

![CI](https://github.com/AreteDriver/frontier-tribe-os/actions/workflows/ci.yml/badge.svg)

> Operations platform for EVE Frontier Tribes and Syndicates — a toolkit for civilization.

**EVE Frontier x Sui Hackathon 2026** | March 11-31

**Live Demo**: [Frontend](https://frontend-ten-theta-80.vercel.app) | [API](https://frontier-tribe-os.fly.dev/docs)

## The Problem

EVE Frontier tribes need coordination tools. Who's in the tribe? What are we building? Where's the treasury? Today this is spreadsheets, Discord channels, and manual wallet checks.

## What It Does

Three integrated modules for tribe leaders and officers:

### Census — Who's Here
- EVE Frontier SSO authentication (FusionAuth + Sui zkLogin)
- Member roster with role hierarchy: Leader > Officer > Member > Recruit
- Invite-code join flow with leader/officer approval
- World API sync for tribe and character data

### Forge Planner — What Are We Building
- Production job board (Kanban-style: queued → in_progress → blocked → complete)
- Tribe inventory tracking with upsert
- Role-gated access (members can view, leaders/officers can manage)

### Ledger — Where's The Money
- Real-time Sui wallet balances via JSON-RPC (treasury + individual)
- Transaction history with on-chain verification (tx_digest)
- Frontend wallet connect via @mysten/dapp-kit (client-side signing only)
- Backend never holds private keys

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Frontend (React)                    │
│  React 19 + TypeScript + Tailwind CSS + Vite          │
│  @mysten/dapp-kit for wallet connect                  │
└────────────────┬─────────────────────────────────────┘
                 │ REST API + JWT
┌────────────────┴─────────────────────────────────────┐
│                  Backend (FastAPI)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Census   │  │  Forge   │  │  Ledger  │           │
│  │  Module   │  │  Module  │  │  Module  │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │              │              │                  │
│       v              v              v                  │
│  ┌─────────────────────────────────────────┐         │
│  │         SQLAlchemy (async)              │         │
│  └─────────────────────────────────────────┘         │
└──────┬───────────────────────────────────┬───────────┘
       │                                   │
       v                                   v
  ┌─────────┐                    ┌──────────────────┐
  │PostgreSQL│                    │  External APIs   │
  │ / SQLite │                    │  - World API     │
  └──────────┘                    │  - Sui JSON-RPC  │
                                  └──────────────────┘
```

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

## API Endpoints

| Module | Method | Path | Description |
|--------|--------|------|-------------|
| Auth | POST | `/auth/dev-login` | Dev-mode login |
| Auth | GET | `/auth/login` | SSO redirect |
| Census | POST | `/census/tribes` | Create tribe |
| Census | GET | `/census/tribes/{id}/members` | Roster |
| Census | POST | `/census/tribes/join/{code}` | Request to join |
| Census | PATCH | `/census/tribes/{id}/members/{id}/role` | Change role |
| Forge | POST | `/forge/tribes/{id}/jobs` | Create job |
| Forge | GET | `/forge/tribes/{id}/jobs` | Job board |
| Forge | PUT | `/forge/tribes/{id}/inventory` | Upsert inventory |
| Ledger | GET | `/ledger/tribes/{id}/balances` | Treasury balance |
| Ledger | POST | `/ledger/tribes/{id}/transactions` | Record tx |

Full API docs at `/docs` (Swagger UI) when running.

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19 + TypeScript + Tailwind CSS v4 + Vite |
| Backend | FastAPI + SQLAlchemy async + Pydantic v2 |
| Database | PostgreSQL (prod) / SQLite (dev/demo) |
| Auth | EVE Frontier FusionAuth SSO + JWT |
| Blockchain | Sui JSON-RPC + @mysten/dapp-kit |
| CI/CD | GitHub Actions (lint + test + security) |
| Deploy | Fly.io |

## Testing

63 tests covering all 3 modules:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest --cov=app -v
```

Tests use in-memory SQLite — no external services required.

## What Makes This Different

- **No custodial wallets**: Backend records transactions but never holds keys. All signing is client-side via dapp-kit.
- **World API integration**: Syncs tribes and characters directly from EVE Frontier's blockchain gateway.
- **Role-gated everything**: Every endpoint enforces tribe membership and role hierarchy.
- **Modular by design**: Census, Forge, and Ledger are independent. Breaking one doesn't break the others.

## License

MIT
