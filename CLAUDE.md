# CLAUDE.md — frontier-tribe-os

## Project Overview

> Operations platform for EVE Frontier Tribes and Syndicates — a toolkit for civilization.

**Hackathon**: EVE Frontier x Sui Hackathon 2026 (March 11-31)

## Current State

- **Files**: 58 across 5 languages (Python, TypeScript, JavaScript, HTML, CSS)
- **Lines**: 6,745
- **Tests**: 0 (adding)
- **CI**: None (adding)

## Architecture

```
frontier-tribe-os/
├── backend/
│   ├── alembic/             # DB migrations (Alembic)
│   ├── app/
│   │   ├── api/             # External API clients (frontier.py, sui.py)
│   │   ├── auth/            # SSO, JWT, middleware
│   │   ├── db/              # Models, session
│   │   ├── modules/
│   │   │   ├── census/      # Auth, roster, roles, join requests
│   │   │   ├── forge/       # Production jobs, inventory
│   │   │   └── ledger/      # Sui treasury (Week 3)
│   │   ├── config.py
│   │   └── main.py
│   ├── data/                # Static fallback JSON (blueprints.json)
│   └── tests/               # pytest (adding)
├── frontend/
│   └── src/
│       ├── pages/           # Landing, Dashboard, Roster, Production, Treasury
│       ├── api.ts           # Axios client + JWT interceptor
│       ├── App.tsx          # Routes + ProtectedRoute
│       └── main.tsx         # Entry point + Sui providers
├── docker-compose.yml       # Full stack (PostgreSQL, Redis, backend, frontend)
├── .env.example
└── .github/workflows/       # CI (adding)
```

## Tech Stack

- **Backend**: FastAPI (Python 3.12), SQLAlchemy async, PostgreSQL, Redis, Alembic
- **Frontend**: React 19 + TypeScript + Tailwind CSS v4 + Vite + React Router
- **Auth**: EVE Frontier FusionAuth SSO + JWT + dev-login bypass
- **Blockchain**: Sui TypeScript SDK (@mysten/sui, @mysten/dapp-kit)
- **Infra**: Docker, GitHub Actions

## Modules (Build Order)

1. **Census** (COMPLETE) — Auth, member roster, roles, join requests, World API sync
2. **Forge** (COMPLETE) — Production job board (Kanban), inventory tracking
3. **Ledger** (Week 3) — Sui token treasury, balances, transactions

**Key rule**: Modules are independent — Ledger not being ready must not break Census/Forge.

## Commands

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Docker (full stack)
docker-compose up

# Tests
cd backend && pytest --cov=app -v

# Lint
ruff check backend/ && ruff format --check backend/
```

## Key Rules

- Every route needs auth middleware — no unauthenticated access to tribe data
- All World API calls must have try/except + static data fallback
- Dev-login is enabled when ENVIRONMENT=development
- Never hardcode credentials
- Wallet signing is frontend-only — backend never holds private keys
- Store entity IDs and token amounts as strings (overflow risk)
- Filter null addresses (0x0000...0000)
- Handle "DEFAULT" character name from World API as None

## API Endpoints

### Auth
- `POST /auth/dev-login?name=Pilot` — Dev-mode login
- `GET /auth/login` — SSO redirect
- `GET /auth/callback?code=...` — SSO callback

### Census
- `POST /census/tribes` — Create tribe (creator becomes leader)
- `GET /census/tribes/{id}` — Get tribe details
- `GET /census/tribes/{id}/members` — List roster
- `POST /census/tribes/join/{invite_code}` — Request to join
- `GET /census/tribes/{id}/requests` — List pending join requests
- `POST /census/tribes/{id}/requests/{id}` — Approve/deny
- `PATCH /census/tribes/{id}/members/{id}/role` — Change role
- `POST /census/sync/tribes` — Sync tribes from World API
- `POST /census/sync/tribes/{id}/members` — Sync members

### Forge
- `POST /forge/tribes/{id}/jobs` — Create production job
- `GET /forge/tribes/{id}/jobs` — List jobs (Kanban)
- `PATCH /forge/tribes/{id}/jobs/{id}` — Update job status
- `DELETE /forge/tribes/{id}/jobs/{id}` — Delete job (leader/officer)
- `PUT /forge/tribes/{id}/inventory` — Upsert inventory item
- `GET /forge/tribes/{id}/inventory` — List inventory

### Ledger
- `GET /ledger/status` — Module health
- `GET /ledger/tribes/{id}/balances` — Treasury balances (on-chain)
- `GET /ledger/members/me/balances` — My wallet balances
- `GET /ledger/tribes/{id}/transactions` — Transaction history
- `POST /ledger/tribes/{id}/transactions` — Record completed tx
- `GET /ledger/tribes/{id}/members/{id}/balances` — Member balances

## Coding Standards

- **Naming**: snake_case (Python), camelCase (TypeScript)
- **Quotes**: double quotes
- **Type hints**: required everywhere
- **Imports**: absolute
- **Paths**: pathlib.Path
- **Line length**: 90 chars (p95)
- **Linting**: ruff check + ruff format

## Anti-Patterns (Do NOT Do)

- Do NOT commit secrets, API keys, or credentials
- Do NOT skip tests for new code
- Do NOT use `any` type — define proper interfaces
- Do NOT use bare `except:` — catch specific exceptions
- Do NOT use `print()` for logging — use `logging` module
- Do NOT hardcode secrets in Dockerfiles — use env vars
- Do NOT use `latest` tag — pin versions
- Do NOT use mutable default arguments
- Do NOT use blocking HTTP calls in async contexts

## Key Models

- `Tribe` — world_tribe_id, name, name_short, leader_address, invite_code, token_contract_address
- `Member` — wallet_address (unique, 0x hex), character_name, smart_character_id, role, timezone
- `JoinRequest` — tribe, wallet_address, status (pending/approved/denied)
- `ProductionJob` — tribe, creator, assignee, type_id, blueprint_name, quantity, status, materials_ready
- `TribeInventory` — unique(tribe_id, item_id), quantity, volume_per_unit
- `LedgerTransaction` — tx_digest (Sui), from/to address, amount (string), coin_type, memo, status

## Roles

`leader` > `officer` > `member` > `recruit`

- Only leaders can promote to officer
- Leaders cannot be demoted
- Join requests require leader/officer approval

## External APIs

- **World API**: `https://blockchain-gateway-stillness.live.tech.evefrontier.com` (public, no auth)
- **FusionAuth SSO**: `https://auth.evefrontier.com/oauth2/` (authorize, token, userinfo)
- **Sui JSON-RPC**: `https://fullnode.mainnet.sui.io:443` (balance, transactions)

## Git Conventions

- Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- Branch naming: `feat/description`, `fix/description`
- Run tests before committing
