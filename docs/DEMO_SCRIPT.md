# Frontier Tribe OS — Demo Script

> 3-minute walkthrough for EVE Frontier x Sui Hackathon judges.

## Setup

- **Frontend**: https://frontend-ten-theta-80.vercel.app
- **API Docs**: https://frontier-tribe-os.fly.dev/docs
- **Dev Login**: `POST /auth/dev-login?name=YourName` (returns JWT)

## Flow

### 1. Authentication (30s)

1. Open the landing page
2. Click **Dev Login** (or SSO if FusionAuth is configured)
3. You're redirected to the Dashboard

**Key point**: EVE Frontier SSO via FusionAuth + Sui zkLogin. Dev-login for demo convenience.

### 2. Census — Create a Tribe (45s)

1. On Dashboard, enter tribe name + tag (e.g. "Frontier Builders" / "FBLD")
2. Click **Create Tribe**
3. Note the **invite code** — copy it
4. View the **Roster** — you're the Leader
5. Open a second browser/incognito, dev-login as a different pilot
6. Use the invite code to **Request to Join**
7. Back in the first browser, approve the join request
8. Roster now shows 2 members with role badges

**Key point**: Role hierarchy (Leader > Officer > Member > Recruit). Leaders approve joins, promote/demote members.

### 3. Forge — Production Planning (45s)

1. Navigate to **Forge Planner**
2. Create a production job: pick a blueprint, set quantity
3. Job appears in **Queued** column
4. Drag/click to move through: Queued → In Progress → Complete
5. Mark materials as ready (green checkmark)
6. Show the tribe **Inventory** (upsert items)

**Key point**: Kanban-style job board. Role-gated — members view, leaders/officers manage.

### 4. Ledger — Treasury (45s)

1. Navigate to **Ledger**
2. Connect Sui wallet (via dapp-kit button)
3. View **Treasury Balance** — real-time from Sui JSON-RPC
4. View **Transaction History** with on-chain tx digests
5. Record a transaction (backend records, frontend signs)

**Key point**: Non-custodial. Backend never holds private keys. All signing is client-side via @mysten/dapp-kit.

### 5. Architecture Highlights (15s)

- 3 independent modules — Census, Forge, Ledger
- World API sync for tribe/character data
- 63 tests, CI pipeline (lint + test + security audit)
- FastAPI + React + Sui SDK
- Deployed: Fly.io (backend) + Vercel (frontend)

## Talking Points

- **Problem**: EVE Frontier tribes coordinate via spreadsheets and Discord. No integrated ops tool.
- **Solution**: Role-gated ops platform with on-chain treasury visibility.
- **Differentiator**: Non-custodial wallet integration. Backend records, never signs.
- **Tech**: FastAPI, React 19, Sui JSON-RPC, World API, FusionAuth SSO.
- **Extensibility**: Modular design — add new modules without touching existing ones.
