# CLAUDE.md — frontier-tribe-os

## Project Overview

![CI](https://github.com/AreteDriver/frontier-tribe-os/actions/workflows/ci.yml/badge.svg)

## Current State

- **Language**: Python, TypeScript
- **Tests**: 180+
- **Modules**: Census, Forge, Ledger, Watch, Intel, Alerts, Warden
- **Deploy**: Fly.io (backend) + Vercel (frontend)

## Architecture

```
frontier-tribe-os/
├── .github/
│   └── workflows/
├── backend/
│   ├── alembic/
│   ├── app/
│   ├── data/
│   └── tests/
├── docs/
├── frontend/
│   ├── .vercel/
│   ├── public/
│   └── src/
├── .env.example
├── .gitignore
├── .gitleaks.toml
├── CLAUDE.md
├── Dockerfile
├── README.md
├── docker-compose.yml
├── fly.toml
```

## Tech Stack

- **Language**: Python 3.12, TypeScript, JavaScript, HTML, CSS
- **Backend**: FastAPI + SQLAlchemy 2.0 async + Pydantic v2
- **Frontend**: React 19 + Tailwind CSS v4 + Vite
- **Auth**: PyJWT (replaced python-jose due to CVE)
- **HTTP**: httpx (async)
- **Charts**: recharts (System Intelligence page)
- **LLM**: Anthropic API via httpx (claude-haiku-4-5)
- **Runtime**: Docker
- **CI/CD**: GitHub Actions (ruff + pytest + pip-audit)
- **Database**: PostgreSQL (prod) / SQLite (dev/test)

## Coding Standards

- **Naming**: snake_case
- **Quote Style**: double quotes
- **Type Hints**: present
- **Imports**: absolute
- **Path Handling**: pathlib
- **Semicolons**: mixed
- **Line Length (p95)**: 77 characters

## Common Commands

```bash
# docker CMD
["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Security Hardening

**Docs**: `docs/SECURITY.md`, `docs/SECRETS.md`, `docs/FRONTEND_SECURITY.md`, `docs/MOVE_HARDENING.md`

### Active Defenses
- **CSP headers**: `SecurityHeadersMiddleware` in `main.py` — default-src 'self', script-src 'self', frame-ancestors 'none'
- **Security headers**: X-Content-Type-Options, X-Frame-Options, Referrer-Policy on every response
- **Vercel CSP**: `frontend/vercel.json` mirrors backend CSP for static assets
- **CORS**: Whitelist from `CORS_ORIGINS` env var — explicit methods (GET/POST/PATCH/PUT/DELETE/OPTIONS), explicit headers (Content-Type, Authorization)
- **Fail-fast secrets**: `config.py` model_validator raises on missing DATABASE_URL, SECRET_KEY; SSO creds required in non-dev
- **Docker credentials**: `docker-compose.yml` reads POSTGRES_PASSWORD from .env (required, no default)
- **Token handling**: JWT in localStorage (acceptable with CSP), ESI tokens server-side only, never logged
- **SQL injection**: SQLAlchemy ORM everywhere, zero string interpolation in queries
- **XSS**: No `dangerouslySetInnerHTML`, all external data rendered as React text nodes

### Rules
- Never hardcode credentials — use env vars, fail fast if missing
- Never store capabilities (AdminCap) in shared objects
- All Move entry functions must have explicit access control assertions
- All ESI/Sui RPC calls proxied through backend — frontend never calls external APIs directly
- Rotate any key that touches a public repo immediately

## Anti-Patterns (Do NOT Do)

- Do NOT commit secrets, API keys, or credentials
- Do NOT skip writing tests for new code
- Do NOT use `any` type — define proper type interfaces
- Do NOT use `var` — use `const` or `let`
- Do NOT use `os.path` — use `pathlib.Path` everywhere
- Do NOT use bare `except:` — catch specific exceptions
- Do NOT use mutable default arguments
- Do NOT use `print()` for logging — use the `logging` module
- Do NOT hardcode secrets in Dockerfiles — use environment variables
- Do NOT use `latest` tag — pin specific versions

## Domain Context

### Frontend Pages
- `/dashboard` — Dashboard (summary cards, cycle banner)
- `/roster` — Census (tribe members, roles, join flow)
- `/production` — Forge (production jobs, blueprint detail, gap analysis)
- `/treasury` — Ledger (Sui treasury, wallet balances)
- `/watch` — Watch (C5 orbital zones, scans, clones, crowns, intel brief)
- `/intel` — Intel (kill feed with live polling, pilot search)
- `/intel/pilots/:address` — Pilot Intelligence (K/D, threat level, active hours)
- `/intel/corps/:corpId` — Corp Intelligence (efficiency, top killers, leaderboard)
- `/alerts` — Alerts (Discord webhook config, 6 alert types)
- `/systems` — Systems Intelligence (hotspot table, zone detail, recharts graphs)

### Key Models/Classes
- `Tribe`, `Member`, `JoinRequest` — Census
- `ProductionJob`, `TribeInventory` — Forge
- `LedgerTransaction` — Ledger
- `OrbitalZone`, `FeralAIEvent`, `Scan`, `ScanIntel` — Watch
- `Clone`, `CloneBlueprint`, `Crown` — Watch (C5)
- `Killmail` — Intel (kill feed, pilot/corp profiles)
- `AlertConfig` — Alerts (Discord webhooks)
- `IntelBriefingService` — LLM intel summary
- `WorldAPIPoller` — Background sync (tribes, killmails, assemblies)
- `PilotProfileResponse`, `CorpProfileResponse` — Intel schemas

### Domain Terms
- CD
- CI
- CSS
- EVE
- Forge Planner
- Frontier Tribe
- Frontier Tribes
- GET
- Intel
- JSON
- JWT
- Kill Feed
- Killmail

### API Endpoints
- `/callback`
- `/dev-login`
- `/health`
- `/login`
- `/members/me/balances`
- `/status`
- `/sync/tribes`
- `/sync/tribes/{tribe_id}/members`
- `/tribes`
- `/tribes/join/{invite_code}`
- `/tribes/{tribe_id}`
- `/tribes/{tribe_id}/balances`
- `/tribes/{tribe_id}/inventory`
- `/tribes/{tribe_id}/jobs`
- `/tribes/{tribe_id}/jobs/{job_id}`
- `/tribes/{tribe_id}/gap-analysis`
- `/tribes/{tribe_id}/summary`
- `/blueprints`
- `/intel/killmails` — paginated kill feed, filterable by corp_name, system_id, since
- `/intel/killmails/{kill_id}` — single killmail detail with raw JSON
- `/intel/killmails/stats` — 24h/7d kill counts, hourly breakdown, top systems
- `/intel/briefing` — LLM-powered intel briefing for a zone
- `/intel/briefing/zones` — zones with enough data for briefing
- `/alerts` — CRUD for Discord alert configs
- `/alerts/{alert_id}/test` — send test alert to Discord webhook
- `/intel/pilots/search?q=` — search pilots by name
- `/intel/pilots/{address}` — pilot profile (K/D, threat level, active hours, top systems)
- `/intel/corps/leaderboard` — top 10 corps by kill count
- `/intel/corps/{corp_id}` — corp profile (efficiency, top killers, members)
- `/watch/systems/hotspots` — Top 20 most active zones by scan count (24h), with trend (UP/DOWN/FLAT)
- `/watch/systems/{zone_id}/activity` — Zone activity timeline: hourly scans, threat history, recent scans, active scanners

### Enums/Constants
- `BASE_URL`
- `SSO_AUTHORIZE_URL`
- `SSO_TOKEN_URL`
- `SSO_USERINFO_URL`
- `TEST_DB_URL`
- `WORLD_API_BASE`

## AI Skills

**Installed**: 122 skills in `~/.claude/skills/`
- `a11y`, `accessibility-checker`, `agent-teams-orchestrator`, `align-debug`, `api-client`, `api-docs`, `api-tester`, `apple-dev-best-practices`, `arch`, `backup`, `brand-voice-architect`, `build`, `changelog`, `ci`, `cicd-pipeline`
- ... and 107 more

**Recommended bundles**: `api-integration`, `full-stack-dev`, `website-builder`

**Recommended skills** (not yet installed):
- `api-integration`
- `full-stack-dev`
- `website-builder`

## LLM Integration (Intel Briefing)

- **Service**: `app/modules/intel/briefing.py` — `IntelBriefingService` calls Anthropic API via httpx (no SDK dependency)
- **Model**: `claude-haiku-4-5-20251001` for speed/cost
- **Config**: `ANTHROPIC_API_KEY` env var (optional — returns mock brief if empty)
- **Cache**: 15-minute in-memory dict cache per zone+hours_back key
- **Endpoints**: `POST /intel/briefing`, `GET /intel/briefing/zones`
- **Frontend**: `IntelBrief` component on Watch page — zone selector, generate button, cooldown timer, threat level badge
- **System prompt**: EVE Frontier intelligence officer persona, military brevity, actionable FC briefs
- **Fallback**: No API key = mock response with `threat_level: UNKNOWN`; API errors logged, never crash

## Git Conventions

- Commit messages: Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)
- Branch naming: `feat/description`, `fix/description`
- Run tests before committing
