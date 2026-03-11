# EVE Frontier x Sui Hackathon 2026 -- Submission

## Project Name

Frontier Tribe OS

## Tagline

"The operating system for EVE Frontier tribes -- Census, Forge, Ledger, Watch"

## Category

Infrastructure / Tooling

## Problem Statement

Tribes in EVE Frontier lack coordination tools. No shared production queue, no treasury visibility, no threat intel sharing. Every tribe reinvents the spreadsheet. Leaders juggle Discord channels, manual wallet checks, and guesswork about who is building what, where resources are, and whether the orbital perimeter is secure. There is no integrated operations platform for tribe management.

## Solution

Frontier Tribe OS provides four integrated modules that give tribe leaders a single pane of glass for operations:

- **Census** -- Member roster with World API sync, role hierarchy (Leader > Officer > Member > Recruit), invite-code join flow with approval workflow, activity tracking, and ship class roles.

- **Forge** -- Production queue with blueprint picker, Kanban-style job board (queued > in_progress > blocked > complete), tribe inventory tracking, material gap analysis showing what is missing per job, and member assignment.

- **Ledger** -- Sui on-chain treasury tracking via JSON-RPC (`suix_getAllBalances`, `suix_getBalance`), per-member wallet balances, transaction history with `tx_digest` verification. Non-custodial: backend records transactions but never holds private keys. All signing is client-side via `@mysten/dapp-kit`.

- **Watch** -- C5 orbital zone monitoring built for the Shroud of Fear cycle. Includes the Signature Resolution System with graduated detection levels (UNRESOLVED > PARTIAL > IDENTIFIED > FULL_INTEL) across four signature types (EM, HEAT, GRAVIMETRIC, RADAR). Feral AI threat tracking with tier escalation (DORMANT > ACTIVE > EVOLVED > CRITICAL), clone reserve monitoring, crown roster, blind spot detection for zones not scanned in 20+ minutes, and Discord webhook alerts for hostile scans, AI evolution events, and low clone reserves.

- **Intel** -- Kill feed with live polling (30s refresh), corp/system filtering, 24h/7d stats with hourly breakdowns and top systems. LLM-powered intel briefings via Claude Haiku -- zone selector, threat assessment, recommended actions, 15-minute cooldown cache. System Intelligence dashboard with hotspot table (top 20 zones by 24h scan count, trend indicators), zone detail with recharts graphs (hourly activity, threat history, scanner leaderboard).

- **Alerts** -- Discord webhook alert configuration with 6 alert types (HOSTILE_SCAN, FERAL_AI_EVOLUTION, BLIND_SPOT, LOW_CLONES, ZONE_CRITICAL, KILL_DETECTED). Per-alert enable/disable, cooldown timers, threshold settings, webhook test button.

- **Warden** -- Defense module scaffold for Move smart contract security patterns (AdminCap, flag-before-effects, checks-then-acts).

## Architecture

```
Frontend (React 19 + TypeScript + Tailwind CSS v4 + Vite)
    |
    | REST API + JWT
    v
Backend (FastAPI + SQLAlchemy 2.0 async + Pydantic v2)
    |
    +-- Census Module    -- member auth, roster, roles, join flow
    +-- Forge Module     -- jobs, inventory, gap analysis, blueprints
    +-- Ledger Module    -- Sui balances, transactions, wallet connect
    +-- Watch Module     -- zones, scans, clones, crowns, alerts
    +-- Warden Module    -- Move contract security scaffold
    +-- Notifications    -- Discord webhook alerts
    +-- World API Poller -- background sync of tribes, characters, assemblies
    |
    +-- PostgreSQL (prod) / SQLite (dev/demo)
    +-- Sui JSON-RPC (suix_getAllBalances, suix_getBalance, suix_queryTransactionBlocks)
    +-- FusionAuth OAuth2 + Sui zkLogin
```

**Deployment**: Fly.io (backend) + Vercel (frontend)

## How It Uses Sui

- **Wallet Connect**: Frontend uses `@mysten/dapp-kit` for client-side Sui wallet connection.
- **Balance Queries**: Backend calls `suix_getAllBalances` and `suix_getBalance` via Sui JSON-RPC to show real treasury and member balances.
- **Transaction History**: `suix_queryTransactionBlocks` with on-chain `tx_digest` verification.
- **Non-custodial**: Backend records transactions but never holds private keys. All signing happens client-side.
- **zkLogin**: Identity derived via Mysten Labs Enoki API -- OAuth identity maps to a Sui wallet address with zero-knowledge proofs.

## How It Uses EVE Frontier

- **FusionAuth SSO**: OAuth2 login via `auth.evefrontier.com` (not CCP's legacy SSO).
- **World API Sync**: Background poller pulls tribe data, smart characters, smart assemblies, and killmails from the blockchain gateway (`blockchain-gateway-stillness.live.tech.evefrontier.com`).
- **Smart Character Lookup**: Maps wallet addresses to in-game identities via `/v2/smartcharacters`.
- **Tribe Data**: `/v2/tribes` endpoint for tribe membership sync.
- **Type Definitions**: `/v2/types` for blueprint and material data used in Forge gap analysis.

## Key Differentiators

1. **Gap Analysis** -- "Who is building what, and what is blocking them." Material deficit tracking per production job against tribe inventory. No other tool in the ecosystem does this.

2. **Signature Resolution System** -- Graduated detection (UNRESOLVED > PARTIAL > IDENTIFIED > FULL_INTEL) with EM, HEAT, GRAVIMETRIC, and RADAR signature types. Matches EVE Frontier's C5 passive observation mechanics. Resolution percentage drives intel quality, not binary yes/no scanning.

3. **Discord Integration** -- Real-time webhook alerts for hostile scans, feral AI evolution, blind spots (zones unseen for 20+ minutes), and low clone reserves. Tribe leaders get actionable notifications without polling a dashboard.

4. **LLM Intel Briefings** -- Claude Haiku generates FC-style threat assessments per zone. Includes threat level, recommended actions, and 15-minute cache to prevent API abuse. Mock fallback when no API key is configured.

5. **System Intelligence** -- Hotspot table ranks top 20 zones by scan activity with trend indicators (UP/DOWN/FLAT). Zone detail view shows hourly activity, threat tier history, and scanner leaderboard via recharts graphs.

6. **World API Poller** -- Background sync of tribes, killmails, and assemblies from the blockchain gateway. Killmails persisted to DB with upsert. Data stays fresh without manual refresh.

7. **On-chain Treasury** -- Real Sui balance reads per member via JSON-RPC, not mock data. Non-custodial design -- backend never touches private keys.

8. **Zero Competition** -- No Alliance Auth equivalent exists for EVE Frontier. EF-Map has a blueprint calculator; EVE Vault has inventory management. Neither provides tribe-level coordination, production planning, or threat intel.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language (Backend) | Python 3.12 |
| Framework (Backend) | FastAPI + Pydantic v2 |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL (prod) / SQLite (dev/demo) |
| HTTP Client | httpx (async) |
| Auth (Tokens) | PyJWT |
| Frontend | React 19 + TypeScript |
| Styling | Tailwind CSS v4 |
| Build | Vite |
| Wallet | @mysten/dapp-kit |
| Blockchain | Sui JSON-RPC |
| Charts | recharts (frontend) |
| LLM | Anthropic API (claude-haiku-4-5) via httpx |
| Notifications | Discord webhooks (httpx) |
| CI/CD | GitHub Actions (ruff lint + pytest + pip-audit) |
| Deploy (Backend) | Fly.io |
| Deploy (Frontend) | Vercel |

## API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/dev-login` | Dev-mode login (returns JWT) |
| GET | `/auth/login` | SSO redirect to FusionAuth |
| GET | `/auth/callback` | OAuth2 callback |

### Census
| Method | Path | Description |
|--------|------|-------------|
| POST | `/census/tribes` | Create tribe |
| GET | `/census/tribes/{id}` | Tribe details |
| GET | `/census/tribes/{id}/members` | Member roster |
| POST | `/census/tribes/join/{code}` | Request to join via invite code |
| PATCH | `/census/tribes/{id}/members/{id}/role` | Change member role |

### Forge
| Method | Path | Description |
|--------|------|-------------|
| POST | `/forge/tribes/{id}/jobs` | Create production job |
| GET | `/forge/tribes/{id}/jobs` | Job board |
| PUT | `/forge/tribes/{id}/inventory` | Upsert tribe inventory |
| GET | `/forge/tribes/{id}/gap-analysis` | Material gap analysis |
| GET | `/forge/blueprints` | Available blueprints |

### Ledger
| Method | Path | Description |
|--------|------|-------------|
| GET | `/ledger/tribes/{id}/balances` | Treasury balance (Sui JSON-RPC) |
| POST | `/ledger/tribes/{id}/transactions` | Record transaction |
| GET | `/ledger/members/me/balances` | Current member balance |

### Watch
| Method | Path | Description |
|--------|------|-------------|
| GET | `/watch/cycle` | Current cycle info (C5) |
| GET | `/watch/orbital-zones` | List zones with threat levels |
| POST | `/watch/orbital-zones` | Create orbital zone |
| GET | `/watch/orbital-zones/{id}/history` | Feral AI event history |
| POST | `/watch/scans` | Submit void scan with signature + resolution |
| GET | `/watch/scans/feed` | Live scan feed (filterable) |
| GET | `/watch/clones` | Clone status and manufacturing queue |
| GET | `/watch/crowns/roster` | Crown roster and type distribution |
| GET | `/watch/alerts/blind-spots` | Zones not scanned in 20+ min |
| GET | `/watch/systems/hotspots` | Top 20 zones by 24h scan count |
| GET | `/watch/systems/{zone_id}/activity` | Zone activity timeline + graphs |

### Intel
| Method | Path | Description |
|--------|------|-------------|
| GET | `/intel/killmails` | Paginated kill feed (filterable) |
| GET | `/intel/killmails/{kill_id}` | Single killmail detail |
| GET | `/intel/killmails/stats` | 24h/7d counts, hourly breakdown, top systems |
| POST | `/intel/briefing` | LLM-generated threat assessment |
| GET | `/intel/briefing/zones` | Zones eligible for briefing |

### Alerts
| Method | Path | Description |
|--------|------|-------------|
| GET | `/alerts` | List alert configs |
| POST | `/alerts` | Create alert config |
| PATCH | `/alerts/{id}` | Update alert config |
| DELETE | `/alerts/{id}` | Delete alert config |
| POST | `/alerts/{id}/test` | Test Discord webhook |

## How to Run

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in secrets
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install && npm run dev

# Full stack with Docker
cp .env.example .env
docker-compose up
```

Dev login: `POST http://localhost:8000/auth/dev-login?name=YourName`

## Test Coverage

```
180+ tests passing
Modules covered: census, forge, ledger, watch, intel (killmails, pilots, corps, battles, briefing), alerts, auth, notifications, poller, world_api
CI pipeline: ruff lint + pytest + pip-audit security scan
Zero code scanning alerts, zero dependabot alerts
```

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest --cov=app -v
```

## Security

- CSP headers on every response (SecurityHeadersMiddleware)
- X-Content-Type-Options, X-Frame-Options, Referrer-Policy
- CORS whitelist from environment variable
- Fail-fast secret validation (Pydantic model_validator)
- SQLAlchemy ORM everywhere -- zero string interpolation in queries
- No `dangerouslySetInnerHTML` in frontend
- JWT auth required on all tribe data endpoints
- Non-custodial wallet design -- backend never holds private keys
- gitleaks + dependabot + pip-audit in CI

## Demo

(Link to demo video -- TODO before March 31)

## Screenshots

To capture screenshots for submission, visit each page after seeding demo data:

1. **Dashboard** — `https://frontend-ten-theta-80.vercel.app/dashboard` (summary cards, cycle banner)
2. **Roster** — `/roster` (4 members with role badges)
3. **Forge** — `/production` (3 jobs in different states, blueprint detail)
4. **Treasury** — `/treasury` (Sui balance display)
5. **Watch** — `/watch` (orbital zones with threat levels, scan feed with signature types, intel brief panel)
6. **Intel** — `/intel` (kill feed with color coding, stats panel, pilot search)
7. **Pilot Profile** — `/intel/pilots/0x1111111111111111111111111111111111111111` (Asterix stats)
8. **Systems** — `/systems` (hotspot table with trends, zone detail graphs)
9. **Alerts** — `/alerts` (alert configs with toggle switches)

Dev login: `POST https://frontier-tribe-os.fly.dev/auth/dev-login?name=Asterix`

## Team

**AreteDriver** -- Solo builder. 17 years enterprise operations (IBM, manufacturing, logistics). Now building AI and blockchain tools.

## Links

- **GitHub**: https://github.com/AreteDriver/frontier-tribe-os
- **Live Frontend**: https://frontend-ten-theta-80.vercel.app
- **Live API**: https://frontier-tribe-os.fly.dev/docs
- **API Swagger**: https://frontier-tribe-os.fly.dev/docs
