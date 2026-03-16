# Frontier Tribe OS

![CI](https://github.com/AreteDriver/frontier-tribe-os/actions/workflows/ci.yml/badge.svg)

> Full-stack tribe and corp management platform for EVE Frontier — census, production, treasury, intel, and threat analysis in one place.

**EVE Frontier x Sui Hackathon 2026** | March 11-31

---

## Live Demo

| | URL |
|--|-----|
| **Frontend** | [frontier-tribe-os on Vercel](https://frontend-ten-theta-80.vercel.app) |
| **API Docs** | [frontier-tribe-os.fly.dev/docs](https://frontier-tribe-os.fly.dev/docs) |

**To try it:** Click the **Dev Login** button on the landing page. No wallet or SSO required. You get a full session with access to all 7 modules.

---

## Modules

| Module | What it does |
|--------|-------------|
| **Census** | Tribe roster and role management (Leader > Officer > Member > Recruit). Invite codes, join approval, World API sync. |
| **Forge** | Production job board (queued / in_progress / blocked / complete). Tribe inventory tracking with upsert. |
| **Ledger** | Real-time Sui wallet balances via JSON-RPC. Transaction history with on-chain `tx_digest` verification. No custodial keys. |
| **Watch** | Orbital zone monitoring and scan tracking. Active scanner registry with hourly activity windows. |
| **Intel** | Kill feed with pilot and corp deep-dives. Battle report reconstruction with timeline and side analysis. Corp leaderboard. |
| **Alerts** | Configurable Discord webhook alerts for kill events, threat escalations, and blind-spot detection. |
| **Warden** | LLM-powered threat analysis. FC briefings with zone-level risk assessment and hypothesis evaluation. |

**Global Search** spans all modules from a single input.

---

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                   Frontend (Vercel)                        │
│  React 19 · TypeScript · Tailwind v4 · Vite               │
│  @mysten/dapp-kit · EF-Map embed · Vercel Analytics       │
└──────────────────────┬────────────────────────────────────┘
                       │ REST + JWT
┌──────────────────────┴────────────────────────────────────┐
│                   Backend (Fly.io)                         │
│  FastAPI · SQLAlchemy async · Pydantic v2                  │
│                                                            │
│  ┌────────┐ ┌───────┐ ┌────────┐ ┌───────┐ ┌───────┐    │
│  │ Census │ │ Forge │ │ Ledger │ │ Watch │ │ Intel │    │
│  └────┬───┘ └───┬───┘ └───┬────┘ └───┬───┘ └───┬───┘    │
│  ┌────┴───┐ ┌───┴────┐                                    │
│  │ Alerts │ │ Warden │  (LLM briefings via Anthropic)     │
│  └────────┘ └────────┘                                    │
│       │          │          │          │          │        │
│       v          v          v          v          v        │
│  ┌────────────────────────────────────────────────┐       │
│  │            SQLAlchemy (async engine)            │       │
│  └────────────────────────────────────────────────┘       │
└───────┬──────────────────────────────────┬────────────────┘
        │                                  │
        v                                  v
   ┌──────────┐                  ┌──────────────────┐
   │PostgreSQL│                  │  External APIs   │
   │ / SQLite │                  │  · World API     │
   └──────────┘                  │  · Sui JSON-RPC  │
                                 │  · Anthropic     │
                                 │  · EF-Map        │
                                 └──────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Tailwind CSS v4, Vite |
| Backend | FastAPI, SQLAlchemy async, Pydantic v2, Python 3.12 |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Auth | Dev-login (hackathon) + JWT sessions |
| Blockchain | Sui JSON-RPC, @mysten/dapp-kit (client-side signing) |
| LLM | Anthropic Claude (Warden briefings) |
| Map | EF-Map embed for system visualization |
| CI/CD | GitHub Actions (lint + test + security) |
| Deploy | Fly.io (backend), Vercel (frontend) |

---

## Getting Started

### Full stack (Docker)

```bash
git clone https://github.com/AreteDriver/frontier-tribe-os.git
cd frontier-tribe-os
cp .env.example .env
docker-compose up
```

### Manual

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Dev login (no SSO needed):

```bash
curl -X POST http://localhost:8000/auth/dev-login?name=YourName
```

---

## API Documentation

Interactive Swagger UI available at `/docs` on any running instance:

- **Local**: http://localhost:8000/docs
- **Production**: https://frontier-tribe-os.fly.dev/docs

---

## Tests

210 tests (195 backend + 15 frontend). All use in-memory SQLite — no external services required.

```bash
# Backend
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest --cov=app -v

# Frontend
cd frontend
npm test
```

---

## What Sets This Apart

- **No custodial wallets** — Backend records transactions but never holds keys. All signing is client-side via dapp-kit.
- **LLM-powered FC briefings** — Warden module generates zone-level threat analysis and tactical recommendations using Claude.
- **7 modules, one platform** — Census, Forge, Ledger, Watch, Intel, Alerts, and Warden work together with shared context and global search.
- **World API + Sui chain integration** — Syncs tribes, characters, and wallet data directly from EVE Frontier's blockchain layer.
- **Dev-login for judges** — One click to a full session. No wallet setup, no SSO dance.

---

## License

MIT

---

Built by [AreteDriver](https://github.com/AreteDriver) for the **EVE Frontier x Sui Hackathon 2026**.
