# FRONTIER TRIBE OS — Claude Code Build Spec
## EVE Frontier × Sui Hackathon 2026 | "A Toolkit for Civilization"
### Hackathon Window: March 11–31, 2026 | Prize Pool: $80,000 USD
### Pre-Hackathon Prep: March 8–10 (3 days — starting NOW)

---

## STRATEGIC CONTEXT

**Why this project wins:**

1. **Directly answers the theme** — "Toolkit for Civilization" is literally what Tribe/Syndicate management is. We aren't stretching to fit.
2. **Zero competition** — No Alliance Auth equivalent exists for EVE Frontier. This is the most-requested missing tool in the ecosystem.
3. **Community vote advantage** — Judging includes community voting. A tool that active tribe leaders can use immediately during the 20-day window gets organic votes.
4. **Long-term monetizable** — This is a SaaS product after the hackathon, not a throwaway demo. $15–30/mo per tribe.
5. **Our edge** — 14 years of EVE experience, corps/alliance management knowledge, Toyota ops background. We understand what tribe leaders actually need.

---

## COMPETITION ASSESSMENT

| Tool | What It Does | Gap We Fill |
|---|---|---|
| EF-Map | Star map, blueprint calc, killboard | No org management |
| EVE Data Core | On-chain block explorer | No player-facing ops |
| EVE Vault (official) | Inventory management | No tribe coordination |
| None | Tribe auth / member management | **THIS IS US** |

**Verdict: Build this. The space is empty.**

---

## HACKATHON vs. ALTERNATIVES COMPARISON

| Axis | Tribe OS (This) | Forge Standalone | Market Tool |
|---|---|---|---|
| Hackathon theme fit | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Competition | None | EF-Map has blueprint calc | None |
| Community vote appeal | High — tribe leaders vote | Medium — industrialists | Medium |
| 20-day buildability | ✅ MVP achievable | ✅ Achievable | ✅ Achievable |
| Long-term revenue | $$$$ SaaS per tribe | $$$ Freemium | $$$ Freemium |
| Our differentiation | Very high | High | Medium |

**Verdict: Tribe OS is the highest value target AND the strongest hackathon submission.**

---

## WHAT WE ARE BUILDING

**Frontier Tribe OS** — A web-based operations platform for EVE Frontier Tribes and Syndicates.

Three integrated modules built in priority order for the 20-day window:

---

## MODULE 1: CENSUS (Auth + Identity)
**Priority: CRITICAL — Build first (Days 1–7)**

The load-bearing foundation. Players log in with their EVE Frontier identity and are assigned a role within their tribe.

### Features
- EVE Frontier SSO / wallet-based login (OAuth2 via official API)
- Member roster with roles: Leader, Officer, Member, Recruit
- Join request queue with approve/deny workflow
- Member activity status (last seen, active/inactive)
- Basic profile: character name, primary ship class, timezone

### Why first
Without auth, nothing else works. This is also the immediate hook for tribe leaders — share a link, onboard members today, get community votes.

---

## MODULE 2: FORGE PLANNER (Production Ops)
**Priority: HIGH — Build second (Days 8–17)**

Tribe-level production coordination. Not a solo blueprint calculator (EF-Map already built that). This is multi-person, multi-job ops management.

### Features
- Production job board: create a job, assign to a member, track status
- Statuses: queued → in_progress → blocked → complete
- Bill of materials pulled from EVE Frontier World API (or static fallback)
- Tribe inventory input: what resources does the tribe currently hold?
- Gap analysis: what's missing to complete the next production run?
- Kanban-style job board UI

### Differentiation from EF-Map
EF-Map tells you *what you need to build X*.
Forge Planner tells you *who is building it, what you already have, and what's blocking you*.
This is the ops layer on top of the calculator layer.

---

## MODULE 3: LEDGER (Token Treasury)
**Priority: MEDIUM — Build third (Days 18–20 if time allows)**

EVE Frontier tribes can issue ERC20 tokens on Sui for governance and resource management. No tool exists to track this.

### Features
- Connect tribe token contract address
- Display token balances per member (read from Sui chain)
- Transaction history feed
- Simple allocation tool: send tokens to member for contributions
- Treasury summary: total supply, in circulation, held by leadership

### Why this matters for hackathon
Most blockchain-native feature in the submission. Directly demonstrates Sui/ERC20 integration. Will stand out to technical judges from Mysten Labs.

---

## TECH STACK

```
Frontend:   React + TypeScript + Tailwind CSS
Backend:    FastAPI (Python)
Database:   PostgreSQL
Cache:      Redis (sessions, API response caching)
Auth:       EVE Frontier SSO (OAuth2)
Blockchain: Sui TypeScript SDK (Ledger module only)
Hosting:    Railway (fast deploy, free tier, Docker support)
API:        EVE Frontier World API (official REST)
```

---

## REPOSITORY STRUCTURE

```
frontier-tribe-os/
├── CLAUDE.md                    # Claude Code context (this file)
├── README.md
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── auth/
│   │   │   ├── sso.py           # EVE Frontier OAuth2 flow
│   │   │   └── middleware.py    # JWT auth middleware
│   │   ├── modules/
│   │   │   ├── census/          # Member auth + roster
│   │   │   │   ├── routes.py
│   │   │   │   └── models.py
│   │   │   ├── forge/           # Production planning
│   │   │   │   ├── routes.py
│   │   │   │   └── models.py
│   │   │   └── ledger/          # Token treasury
│   │   │       ├── routes.py
│   │   │       └── sui_client.py
│   │   ├── api/
│   │   │   └── frontier.py      # World API client wrapper
│   │   └── db/
│   │       ├── models.py
│   │       └── migrations/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.tsx        # Landing + login
│   │   │   ├── dashboard.tsx    # Tribe overview
│   │   │   ├── roster.tsx       # Census module
│   │   │   ├── production.tsx   # Forge Planner
│   │   │   └── treasury.tsx     # Ledger module
│   │   ├── components/
│   │   └── hooks/
│   ├── package.json
│   └── Dockerfile
└── docs/
    ├── API_NOTES.md             # World API findings — document what works/fails
    └── HACKATHON_SUBMISSION.md  # Write-up for judges
```

---

## DATABASE SCHEMA

```sql
-- Tribes
CREATE TABLE tribes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  leader_character_id VARCHAR(100),
  invite_code VARCHAR(32) UNIQUE,           -- For member onboarding link
  token_contract_address VARCHAR(255),      -- For Ledger module
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Members
CREATE TABLE members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tribe_id UUID REFERENCES tribes(id),
  character_id VARCHAR(100) UNIQUE NOT NULL, -- From EVE Frontier SSO
  character_name VARCHAR(255),
  role VARCHAR(50) DEFAULT 'recruit',        -- leader, officer, member, recruit
  timezone VARCHAR(50),
  last_active TIMESTAMPTZ,
  joined_at TIMESTAMPTZ DEFAULT NOW()
);

-- Join Requests
CREATE TABLE join_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tribe_id UUID REFERENCES tribes(id),
  character_id VARCHAR(100),
  character_name VARCHAR(255),
  status VARCHAR(50) DEFAULT 'pending',     -- pending, approved, denied
  requested_at TIMESTAMPTZ DEFAULT NOW()
);

-- Production Jobs (Forge)
CREATE TABLE production_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tribe_id UUID REFERENCES tribes(id),
  assigned_to UUID REFERENCES members(id),
  blueprint_id VARCHAR(100),
  blueprint_name VARCHAR(255),
  quantity INTEGER DEFAULT 1,
  status VARCHAR(50) DEFAULT 'queued',      -- queued, in_progress, blocked, complete
  materials_ready BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Tribe Inventory (Forge)
CREATE TABLE tribe_inventory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tribe_id UUID REFERENCES tribes(id),
  item_id VARCHAR(100),
  item_name VARCHAR(255),
  quantity INTEGER DEFAULT 0,
  updated_by UUID REFERENCES members(id),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## EVE FRONTIER API INTEGRATION

### Endpoints to Verify Day 1 of Hackathon
```
GET /api/v1/characters/{character_id}         # Character info
GET /api/v1/corporations/{corp_id}/members    # Tribe member list
GET /api/v1/universe/types/{type_id}          # Item/blueprint data
GET /api/v1/markets/prices                    # Market price data
```

Base URL: https://api.evefrontier.com (verify at docs.evefrontier.com)

### Auth Flow
1. Redirect player to EVE Frontier SSO endpoint
2. Receive authorization code
3. Exchange for OAuth2 access token
4. Call /verify (or /characters/me) to get character_id + character_name
5. Issue JWT, store session in Redis

### If World API Is Limited or Broken
Document failures in `docs/API_NOTES.md`. Fall back to static blueprint data.
EF-Map likely publishes game data on GitHub — check their repo for JSON item/recipe dumps.
Build UI against static data, swap to live API when confirmed working.

---

## 20-DAY SPRINT PLAN

### PRE-HACKATHON: March 8–10 (NOW)
- [ ] Register at deepsurge.xyz/evefrontier2026
- [ ] Read builder docs: docs.evefrontier.com
- [ ] Join EVE Frontier builder Discord, find #builder-general
- [ ] Confirm World API endpoints that are actually live
- [ ] Set up Railway account + new project
- [ ] Create GitHub repo: `frontier-tribe-os`
- [ ] Scaffold backend (FastAPI + PostgreSQL + Alembic)
- [ ] Scaffold frontend (React + Tailwind + React Router)
- [ ] Set up docker-compose for local dev

### WEEK 1: March 11–17 — CENSUS MVP
- [ ] EVE Frontier SSO OAuth2 login flow working end-to-end
- [ ] Player can create a new tribe
- [ ] Player can join a tribe via invite code
- [ ] Roster page: list members with roles + last active
- [ ] Leader can approve/deny join requests
- [ ] Leader can change member roles
- [ ] Deploy to Railway — get a live URL for community sharing

### WEEK 2: March 18–24 — FORGE PLANNER
- [ ] Production job CRUD (create, assign, update status)
- [ ] Blueprint search (World API or static JSON)
- [ ] Tribe inventory input form (manual entry to start)
- [ ] Gap analysis: required materials vs. tribe inventory
- [ ] Kanban job board UI with drag-or-click status updates
- [ ] Notify assigned member (in-app, not email for now)

### WEEK 3: March 25–31 — POLISH + LEDGER + SUBMIT
- [ ] Ledger: Sui wallet connect (Sui TypeScript SDK)
- [ ] Read ERC20 token balances per member from Sui chain
- [ ] Transaction history display (read-only)
- [ ] UI polish: dark theme, mobile responsive, empty states
- [ ] Write docs/HACKATHON_SUBMISSION.md (narrative for judges)
- [ ] Record 2–3 minute demo video
- [ ] Post to EVE Frontier community for votes (Reddit, Discord)
- [ ] Submit before March 31 deadline

---

## ENVIRONMENT VARIABLES

```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/tribedb
REDIS_URL=redis://localhost:6379
EVE_FRONTIER_CLIENT_ID=your_client_id
EVE_FRONTIER_CLIENT_SECRET=your_client_secret
EVE_FRONTIER_CALLBACK_URL=https://yourdomain.railway.app/auth/callback
SECRET_KEY=your_jwt_signing_secret_min_32_chars
ENVIRONMENT=development

# Frontend
VITE_API_URL=http://localhost:8000
VITE_EVE_FRONTIER_CLIENT_ID=your_client_id
```

---

## CLAUDE CODE OPERATING RULES

When working on this codebase:

1. **Never break auth** — The SSO flow is load-bearing. Run auth tests after every change that touches session or middleware.
2. **Modules must be independent** — Census, Forge, and Ledger import independently. Ledger not being ready must not break Census.
3. **API failures are expected** — Wrap every World API call in try/except. Log to API_NOTES.md what works and what returns 404/403.
4. **Ship working over perfect** — Hackathon deadline is hard. A working join-request flow beats a beautiful broken Kanban.
5. **Every route needs auth middleware** — No unauthenticated access to any tribe data.
6. **Static data fallback always** — If World API is unavailable, load from `backend/data/blueprints.json`. Never block UI on API uncertainty.

---

## KNOWN RISKS + MITIGATIONS

| Risk | Mitigation |
|---|---|
| EVE Frontier SSO docs are sparse | Check builder Discord Day 1; ask community for current OAuth endpoint |
| World API missing endpoints | Build UI against static JSON first; swap to live API when confirmed |
| Sui ERC20 read is complex | Descope Ledger to Week 3 polish; Census + Forge alone win the hackathon |
| 20 days is tight | Census MVP is the minimum viable submission; Forge is the differentiator |
| EF-Map adds tribe features before us | They are a map tool; we are an ops platform; different value prop |

---

## POST-HACKATHON MONETIZATION

| Tier | Price | Features |
|---|---|---|
| Free | $0 | 1 tribe, up to 10 members, Census only |
| Tribe Pro | $15/mo | Unlimited members, Census + Forge + Ledger |
| Syndicate | $49/mo | Up to 10 tribes under one Syndicate, aggregate dashboard, API access |

**Revenue model:** Stripe (leverage existing BenchGoblins Stripe integration knowledge)
**Target:** 100 tribes at Tribe Pro = $1,500/mo ARR within 6 months of launch

---

## RESOURCES

- Hackathon Registration: http://deepsurge.xyz/evefrontier2026
- Builder Docs: https://docs.evefrontier.com
- EVE Frontier Whitepaper (Economy/Tokens): https://whitepaper.evefrontier.com/economy
- Sui TypeScript SDK: https://sdk.mystenlabs.com/typescript
- EF-Map (check GitHub for data structures): https://ef-map.com
- EVE Frontier Discord: Find #builder-general for current SSO auth flow
