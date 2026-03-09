# EVE Frontier x Sui Hackathon 2026 — Submission

## Project Name
Frontier Tribe OS

## Tagline
Operations platform for EVE Frontier Tribes and Syndicates — a toolkit for civilization.

## Category
Infrastructure / Tooling

## Links
- **Live Frontend**: https://frontend-ten-theta-80.vercel.app
- **Live API**: https://frontier-tribe-os.fly.dev/docs
- **GitHub**: https://github.com/AreteDriver/frontier-tribe-os

## What It Does

Frontier Tribe OS gives EVE Frontier tribe leaders three integrated tools:

1. **Census** — Member roster with role hierarchy (Leader > Officer > Member > Recruit), invite-code join flow, and World API character sync
2. **Forge Planner** — Kanban-style production job board with inventory tracking
3. **Ledger** — Real-time Sui wallet balances and transaction history via JSON-RPC, with non-custodial wallet connect

## The Problem

EVE Frontier tribes coordinate through Discord channels, spreadsheets, and manual wallet checks. There's no integrated operations tool. Leaders can't see who's in the tribe, what's being built, and where the treasury stands in one place.

## How It Uses Sui

- **Wallet Connect**: Frontend uses `@mysten/dapp-kit` for client-side Sui wallet connection
- **Balance Queries**: Backend calls `suix_getAllBalances` and `suix_getBalance` via Sui JSON-RPC
- **Transaction History**: `suix_queryTransactionBlocks` with on-chain `tx_digest` verification
- **Non-custodial**: Backend records transactions but never holds private keys. All signing is client-side.

## How It Uses EVE Frontier

- **FusionAuth SSO**: OAuth2 login via `auth.evefrontier.com` (+ Sui zkLogin for wallet derivation)
- **World API Sync**: Pulls tribe data, character profiles, and smart assemblies from the blockchain gateway
- **Smart Character Lookup**: Maps wallet addresses to in-game identities

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Tailwind CSS v4 + Vite |
| Backend | FastAPI + SQLAlchemy async + Pydantic v2 |
| Database | PostgreSQL (prod-ready) / SQLite (demo) |
| Auth | EVE Frontier FusionAuth SSO + JWT |
| Blockchain | Sui JSON-RPC + @mysten/dapp-kit |
| CI/CD | GitHub Actions (lint + test + security audit) |
| Deploy | Fly.io (backend) + Vercel (frontend) |

## Testing

- 63 backend tests covering all 3 modules
- Frontend tests with Vitest + React Testing Library
- CI pipeline: ruff lint, pytest, pip-audit security scan
- Zero code scanning alerts, zero dependabot alerts

## Architecture Highlights

- **Modular**: Census, Forge, and Ledger are independent modules. Breaking one doesn't break the others.
- **Non-custodial**: Backend never touches private keys. Wallet signing happens exclusively in the browser.
- **Graceful degradation**: All World API calls have try/except with static data fallback.
- **Role-gated**: Every endpoint enforces tribe membership and role hierarchy.

## Built By

**AreteDriver** — Solo developer
