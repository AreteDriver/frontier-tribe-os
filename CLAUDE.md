# CLAUDE.md — frontier-tribe-os

## Project Overview

![CI](https://github.com/AreteDriver/frontier-tribe-os/actions/workflows/ci.yml/badge.svg)

## Current State

- **Language**: Python
- **Files**: 94 across 5 languages
- **Lines**: 13,149

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

- **Language**: Python, TypeScript, JavaScript, HTML, CSS
- **Runtime**: Docker
- **CI/CD**: GitHub Actions

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

### Key Models/Classes
- `BalanceResponse`
- `Base`
- `ErrorBoundary`
- `InventoryItem`
- `InventoryResponse`
- `JobCreate`
- `JobResponse`
- `JobUpdate`
- `JoinRequest`
- `JoinRequestAction`
- `JoinRequestResponse`
- `LedgerTransaction`
- `Member`
- `MemberResponse`
- `ProductionJob`

### Domain Terms
- CD
- CI
- CSS
- EVE
- Forge Planner
- Frontier Tribe
- Frontier Tribes
- GET
- JSON
- JWT

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

## Git Conventions

- Commit messages: Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)
- Branch naming: `feat/description`, `fix/description`
- Run tests before committing
