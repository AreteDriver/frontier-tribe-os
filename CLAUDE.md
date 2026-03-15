# CLAUDE.md — frontier-tribe-os

## Project Overview

![CI](https://github.com/AreteDriver/frontier-tribe-os/actions/workflows/ci.yml/badge.svg)

## Current State

- **Language**: Python
- **Files**: 159 across 6 languages
- **Lines**: 28,150

## Architecture

```
frontier-tribe-os/
├── .github/
│   └── workflows/
├── backend/
│   ├── alembic/
│   ├── app/
│   ├── data/
│   ├── scripts/
│   └── tests/
├── contracts/
│   ├── scripts/
│   ├── sources/
│   ├── tests/
│   └── warden/
├── docs/
├── frontend/
│   ├── .vercel/
│   ├── public/
│   └── src/
├── .env.example
├── .gitignore
├── .gitleaks.toml
├── .pre-commit-config.yaml
├── CLAUDE.md
├── Dockerfile
├── README.md
├── docker-compose.yml
├── fly.toml
```

## Tech Stack

- **Language**: Python, TypeScript, Shell, JavaScript, HTML, CSS
- **Runtime**: Docker
- **CI/CD**: GitHub Actions

## Coding Standards

- **Naming**: snake_case
- **Quote Style**: double quotes
- **Type Hints**: present
- **Docstrings**: google style
- **Imports**: absolute
- **Path Handling**: pathlib
- **Line Length (p95)**: 76 characters

## Common Commands

```bash
# docker CMD
["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Anti-Patterns (Do NOT Do)

- Do NOT commit secrets, API keys, or credentials
- Do NOT skip writing tests for new code
- Do NOT use `any` type — define proper type interfaces
- Do NOT use `var` — use `const` or `let`
- Do NOT hardcode secrets in Dockerfiles — use environment variables
- Do NOT use `latest` tag — pin specific versions
- Do NOT use `os.path` — use `pathlib.Path` everywhere
- Do NOT use bare `except:` — catch specific exceptions
- Do NOT use mutable default arguments
- Do NOT use `print()` for logging — use the `logging` module

## Domain Context

### Key Models/Classes
- `ActiveHour`
- `ActiveScannerEntry`
- `AlertConfig`
- `AlertConfigCreate`
- `AlertConfigResponse`
- `AlertConfigUpdate`
- `BalanceResponse`
- `Base`
- `BattleDetailResponse`
- `BattleSide`
- `BattleSummary`
- `BattleTimelineEntry`
- `BriefingRequest`
- `BriefingResponse`
- `BriefingZone`

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
- `/alerts/blind-spots`
- `/alerts/test`
- `/battles`
- `/battles/{battle_id}`
- `/blueprints`
- `/briefing`
- `/briefing/zones`
- `/callback`
- `/clones`
- `/corps/leaderboard`
- `/corps/{corp_id}`
- `/crowns/roster`
- `/cycle`
- `/dev-login`
- `/health`

### Enums/Constants
- `ANTHROPIC_API_URL`
- `ANTHROPIC_MODEL`
- `ANTHROPIC_VERSION`
- `BASE_URL`
- `CYCLE_NAME`
- `CYCLE_RESET_AT`
- `EVALUATE_PROMPT`
- `HYPOTHESIS_PROMPT`
- `SSO_AUTHORIZE_URL`
- `SSO_TOKEN_URL`

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
