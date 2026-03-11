# FRONTIER WATCH — Build Bible
> Operational Intelligence Dashboard for EVE Frontier Corps
> Hackathon Target: March 31, 2026 | Post-Hackathon: Ongoing Platform

---

## What This Is

Frontier Watch is the EVE Frontier equivalent of EVE-Prism's Home Page + System Page + Operative Report — rebuilt for a blockchain-native game where the data is provable, not estimated. It is a read-only external app that ingests EVE Frontier's World API, killmail feed, and on-chain events, then surfaces operational intelligence to corp FCs and leadership.

**Core thesis:** You can't defend what you can't see.

**Prism features this replaces and exceeds:**
- Home Page (live kill feed, filterable by corp/alliance/area)
- System Page (sovereignty, fleet activity, structure kills, active orgs)
- Operative Report (hotspot mapping, activity predictions, low/null entrances)
- Pilot Page (activity zones, estimated budget — now provable from chain)
- Battle Report / Related (timeline reconstruction, fleet compositions)

**What Prism couldn't do that Frontier enables:**
- On-chain kill verification (not zkillboard estimates — provable events)
- Wallet transparency = real pilot ISK flow, not inferred from kill value
- Smart gate activity = actual corp movement patterns
- Storage unit snapshots = real supply chain intelligence
- Sovereign structure ownership = trustless territory control data

---

## Architecture

### System Diagram

```
EVE Frontier World API (REST)
EVE Frontier MUD Indexer (WebSocket / polling)
Killmail feed (on-chain events)
         │
         ▼
┌──────────────────────────────────────┐
│           INGESTION LAYER            │
│  poller.py       — REST polling      │
│  indexer.py      — MUD subscription  │
│  killmail.py     — kill ingestion    │
│  processor.py    — normalization     │
│  notifier.py     — Discord webhooks  │
└─────────────────┬────────────────────┘
                  │ writes
                  ▼
┌──────────────────────────────────────┐
│     SQLite + FTS5 (WAL mode)         │
│  gate_events                         │
│  killmails                           │
│  storage_snapshots                   │
│  characters                          │
│  corps                               │
│  systems                             │
│  alerts                              │
│  activity_heatmap (aggregated)       │
│  gate_events_fts (FTS5 index)        │
└─────────────────┬────────────────────┘
                  │ reads
                  ▼
┌──────────────────────────────────────┐
│          FastAPI REST API            │
│  /api/killmails                      │
│  /api/gates                          │
│  /api/systems/{id}                   │
│  /api/pilots/{id}                    │
│  /api/corps/{id}                     │
│  /api/hotspots                       │
│  /api/alerts                         │
│  /api/intel/summary (LLM endpoint)   │
└─────────────────┬────────────────────┘
                  │ serves
                  ▼
┌──────────────────────────────────────┐
│        React + Tailwind UI           │
│  KillFeed (live, filterable)         │
│  SystemMap (heatmap overlay)         │
│  PilotProfile                        │
│  CorpProfile                         │
│  BattleReport                        │
│  OperativeReport (hotspots)          │
│  AlertConfig                         │
│  IntelSummary (LLM panel)           │
└──────────────────────────────────────┘
         │
         ▼
   Discord Webhooks (alert delivery)
```

### Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Backend | FastAPI + uvicorn | Fast async, you know it, minimal boilerplate |
| Database | SQLite WAL + FTS5 | Zero infra, handles hackathon scale, swap to Postgres post-launch |
| Ingestion | Python polling loop | Reliable, debuggable, WebSocket upgrade path available |
| Frontend | React + Tailwind + recharts | Component reuse, familiar, recharts for time-series |
| Alerts | Discord webhooks | Free, instant, zero infrastructure |
| LLM Layer | Anthropic API | Intel summarization, threat assessment, battle report narrative |
| Deployment | VPS + SQLite persistent | Single-server, simple, hackathon-appropriate |

### Database Schema

```sql
-- Gate traffic events
CREATE TABLE gate_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE,
    gate_id TEXT,
    system_id TEXT,
    character_id TEXT,
    corp_id TEXT,
    direction TEXT,  -- inbound/outbound
    timestamp INTEGER,
    raw_json TEXT
);

-- Killmails — primary positional signal post-coordinate-privacy
CREATE TABLE killmails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kill_id TEXT UNIQUE,
    victim_character_id TEXT,
    victim_corp_id TEXT,
    attacker_character_ids TEXT,  -- JSON array
    attacker_corp_ids TEXT,       -- JSON array
    ship_type_id TEXT,
    system_id TEXT,
    timestamp INTEGER,
    isk_value REAL,
    raw_json TEXT
);

-- Storage unit activity
CREATE TABLE storage_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    storage_id TEXT,
    system_id TEXT,
    owner_corp_id TEXT,
    item_count INTEGER,
    snapshot_time INTEGER,
    delta_items INTEGER,  -- change from last snapshot
    raw_json TEXT
);

-- Character profiles (aggregated from events)
CREATE TABLE characters (
    character_id TEXT PRIMARY KEY,
    character_name TEXT,
    corp_id TEXT,
    sec_status REAL,
    kill_count INTEGER DEFAULT 0,
    death_count INTEGER DEFAULT 0,
    primary_system TEXT,
    active_zones TEXT,     -- JSON array of system_ids
    last_seen INTEGER,
    estimated_isk_flow REAL,
    updated_at INTEGER
);

-- Corp profiles
CREATE TABLE corps (
    corp_id TEXT PRIMARY KEY,
    corp_name TEXT,
    member_count INTEGER,
    kill_count INTEGER DEFAULT 0,
    death_count INTEGER DEFAULT 0,
    primary_systems TEXT,  -- JSON array
    last_active INTEGER,
    updated_at INTEGER
);

-- Aggregated system activity (pre-computed for heatmap)
CREATE TABLE system_activity (
    system_id TEXT PRIMARY KEY,
    system_name TEXT,
    kill_count_24h INTEGER DEFAULT 0,
    kill_count_7d INTEGER DEFAULT 0,
    gate_jumps_24h INTEGER DEFAULT 0,
    active_corps TEXT,     -- JSON array
    controlling_corp TEXT,
    last_event INTEGER,
    updated_at INTEGER
);

-- Alert configuration
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT,  -- kill_threshold, corp_spotted, system_activity
    target_id TEXT,   -- character_id, corp_id, or system_id
    threshold INTEGER,
    discord_webhook TEXT,
    enabled INTEGER DEFAULT 1,
    last_triggered INTEGER
);

-- FTS5 for fast character/corp search
CREATE VIRTUAL TABLE gate_events_fts USING fts5(
    character_id, corp_id, system_id,
    content=gate_events
);
```

---

## Feature Breakdown (Prism → Frontier Watch Mapping)

### Feature 1: Live Kill Feed
**Prism equivalent:** Home Page kill feed (left panel)
**Frontier advantage:** On-chain verified, not zkillboard estimates

What it shows:
- Real-time kill events as they land
- Victim name, corp, ship type, system
- Attacker count and corps involved
- ISK value (where calculable)
- Timestamp and system link

Filters (from Prism's profile system, improved):
- By corp (watch list)
- By system (region of interest)
- By ship class
- By kill value threshold
- Solo vs fleet kills

Discord alert trigger: Any kill matching a watched corp/system fires a webhook with kill summary.

### Feature 2: System Intelligence Page
**Prism equivalent:** System Page (sovereignty + activity graphs + fleet compositions)
**Frontier advantage:** Structure ownership is on-chain, not inferred

What it shows:
- Controlling corp (from Smart Structure ownership)
- Recent kill activity (24h / 7d graphs)
- Gate traffic patterns (who is jumping through)
- Active organizations (corps seen in system last 7 days)
- Last 10 fleets seen active with compositions
- Storage unit activity (supply chain signal)

Sub-tabs (from Prism's structure):
- Activity (graphs + kill feed)
- Fleets (last seen compositions)
- Structures (Smart Assemblies + ownership)

### Feature 3: Pilot Intelligence Page
**Prism equivalent:** Pilot Page
**Frontier advantage:** ISK flow is real wallet data, not estimated from kill values

What it shows:
- Kill / Death ratio
- Primary activity zones (systems)
- Solo vs fleet ratio
- Ship type preferences (from kill history)
- Active hours (timezone inference from kill timestamps)
- Corp history
- Estimated ISK flow (on-chain transactions where visible)
- Threat level indicator (FC, awoxer, cyno, scout markers)

### Feature 4: Corp Intelligence Page
**Prism equivalent:** Corporation Page
**Frontier advantage:** PvP ratings backed by verifiable chain data

What it shows:
- Corp PvP rating (kill efficiency)
- Member activity distribution
- Primary systems of operation
- Most-used ship doctrines (from kill history)
- Command-suitability scores per pilot
- Recent battle history

### Feature 5: Operative Report (Hotspot Map)
**Prism equivalent:** Operative Report
**Frontier advantage:** Prediction layer possible from gate traffic patterns

What it shows:
- Top 20 most active PvP systems (24h)
- Activity trend indicators (rising / falling)
- +1 / +2 hour activity prediction (from historical patterns)
- Entry point mapping (low sec entrances to active null systems)
- Last 10 fleets seen active server-wide

### Feature 6: Battle Report / Incident Reconstruction
**Prism equivalent:** Related (battle report with 3 sides, timelines, ship compositions)
**Frontier advantage:** All data is permanent and verifiable — The Black Box is the evolution of this

What it shows:
- Multi-sided battle timeline
- Ship compositions per side
- Kill sequence reconstruction
- Total ISK destroyed per side
- FC identification (who called the fleet)
- LLM narrative summary of the engagement

### Feature 7: Intel Summary (LLM Layer — Frontier-exclusive)
**No Prism equivalent — this is new**

What it does:
- Takes last 4 hours of activity data for a system/region
- Sends to Anthropic API with structured prompt
- Returns plain-English operational brief:
  - "X corp has been active in [system] for 3 hours with 12 members. Last engagement was a 6v4 at [time]. Primary ship class: cruisers. Recommend avoid or bring equivalent."
- FC briefing mode: paste a fleet, get composition analysis vs recent threats
- Threat pilot brief: paste a character name, get activity summary

---

## Claude Code Session Prompts

### Prompt 1: Project Initialization

```
You are building Frontier Watch — a read-only operational intelligence dashboard
for EVE Frontier corps.

Tech stack:
- Backend: FastAPI + uvicorn, Python 3.11+
- Database: SQLite with FTS5 and WAL mode enabled
- Ingestion: polling EVE Frontier World API REST endpoints
- Frontend: React + Tailwind + recharts
- Alerts: Discord webhooks
- LLM: Anthropic API (claude-sonnet-4-5) for intel summarization
- Deployment: single VPS, persistent SQLite

CLAUDE.md is at the root — read it before any work.

Architecture principles:
- Never crash the poller — all ingestion errors are logged, not raised
- Schema column names must match real API field names — explore before building
- Killmails are the primary positional signal — coordinates may be hidden post-hackathon
- Discord webhook is the alert delivery mechanism — not mobile push, not email
- SQLite WAL mode — enables concurrent reads during writes
- FTS5 index on character/corp fields — enables fast search

Current task: Initialize the project structure. Create:
1. backend/main.py — FastAPI app with CORS, health endpoint
2. backend/db/database.py — SQLite connection, WAL enable, all CREATE TABLE statements
3. backend/ingestion/poller.py — polling loop skeleton with error handling
4. backend/ingestion/processor.py — normalization skeleton
5. backend/ingestion/notifier.py — Discord webhook sender
6. frontend/ — React app scaffold with Tailwind configured
7. CLAUDE.md — project context file

Do not fill in API endpoints yet — skeleton and structure only.
```

### Prompt 2: Ingestion Layer

```
You are working on Frontier Watch. Read CLAUDE.md first.

The ingestion layer needs to poll EVE Frontier's World API and normalize
events into our SQLite schema.

API base URL: https://blockchain-gateway-nova.nursery.reitnorf.com
Known endpoints to try:
- /smartassemblies
- /characters
- /solarsystems
- /killmails (if available)
- /gates
- /storageunits

Current task:
1. Build poller.py to poll each endpoint on a configurable interval (default 60s)
2. Build processor.py to normalize raw API responses into our schema field names
3. Handle rate limits — if 429, back off exponentially, log, continue
4. Handle missing fields gracefully — insert NULL, never crash
5. Write a one-shot explore script that hits all endpoints, prints field names,
   saves sample JSON to docs/api-samples/

All errors go to stderr as structured log lines. Never raise to caller.
```

### Prompt 3: Kill Feed API + Frontend

```
You are working on Frontier Watch. Read CLAUDE.md first.

We need a live kill feed — the core UX of the dashboard.

Backend task:
1. GET /api/killmails — paginated, filterable by corp_id, system_id, min_isk_value,
   timestamp_after. Returns last 100 kills by default.
2. GET /api/killmails/{kill_id} — single kill detail with full attacker list
3. Aggregation query: kill count by system for heatmap data

Frontend task:
1. KillFeed component — polls /api/killmails every 30s, renders scrolling list
2. Each kill row shows: victim name, corp, ship type, system, attacker count, time ago
3. Click a kill row → expand to show full attacker list
4. Filter bar: corp name search, system search, min ISK slider
5. New kills animate in from top (CSS transition, not jarring)
6. Red/orange color coding by ISK value tier

Style: dark background, EVE-appropriate aesthetic — dark greys, amber/orange accents.
No white backgrounds.
```

### Prompt 4: System Intelligence Page

```
You are working on Frontier Watch. Read CLAUDE.md first.

Build the System Intelligence page — the operational picture for a single system.

Backend:
1. GET /api/systems/{system_id} — returns:
   - Controlling corp (from structure ownership)
   - Kill counts (24h, 7d)
   - Gate jump counts (24h if available)
   - Active corps list (seen in last 7 days)
   - Last 10 fleet engagements with compositions
   - Storage unit activity delta (last 24h)
2. Aggregation should be pre-computed by a background task, not on-request

Frontend:
1. SystemPage component with three tabs: Activity | Fleets | Structures
2. Activity tab: kill graph (recharts LineChart), corp list, recent kills
3. Fleets tab: table of last 10 engagements — time, attacker corps, ships used, ISK
4. Structures tab: list of Smart Assemblies, owner, type, last activity

Make system searchable from a top nav search bar (FTS5 query to backend).
```

### Prompt 5: LLM Intel Summary

```
You are working on Frontier Watch. Read CLAUDE.md first.

Build the Intel Summary feature — LLM-generated operational briefs.

Backend:
1. POST /api/intel/summary — accepts { system_id, hours_back: 4 }
2. Queries last N hours of kills, gate events, active corps for that system
3. Formats as structured context block
4. Calls Anthropic API (claude-sonnet-4-5) with this prompt:

SYSTEM PROMPT:
You are an EVE Frontier intelligence officer. You receive raw operational data
and produce concise, actionable fleet commander briefs. Be direct. Use military
brevity. Flag threats, opportunities, and recommended actions.

USER PROMPT:
[Structured data block: kill count, active corps, ship compositions, last engagement time]

Produce an intel brief covering:
1. Threat level (Low/Medium/High/Critical)
2. Active hostile organizations
3. Last known fleet composition and time
4. Recommended action (avoid / scout / engage / fortify)
5. Key intelligence gaps

Keep it under 150 words.

4. Cache result for 15 minutes — don't hammer the API
5. Return { summary: string, threat_level: string, generated_at: timestamp }

Frontend:
1. IntelPanel component — collapsible side panel on SystemPage
2. "Generate Brief" button triggers POST
3. Shows threat level badge (color coded), summary text, timestamp
4. Refresh button with 15-min cooldown indicator
```

### Prompt 6: Discord Alert System

```
You are working on Frontier Watch. Read CLAUDE.md first.

Build the Discord alert system — the notification layer for watched entities.

Backend:
1. Alert types:
   - kill_in_system: {system_id, threshold: min kill count per hour}
   - corp_spotted: {corp_id, system_id} — alert when corp seen in system
   - pilot_spotted: {character_id} — alert when specific pilot seen anywhere
   - structure_threatened: {structure_id} — alert when kills near structure spike

2. Alert evaluation runs every 60s after poller cycle completes
3. Discord webhook payload format:
   {
     "embeds": [{
       "title": "⚠️ INTEL ALERT — [System Name]",
       "color": 15158332,  // red
       "fields": [
         {"name": "Event", "value": "..."},
         {"name": "Details", "value": "..."},
         {"name": "Time", "value": "..."}
       ]
     }]
   }
4. Rate limit: max 1 alert per entity per 5 minutes
5. GET /api/alerts — list configured alerts
6. POST /api/alerts — create alert
7. DELETE /api/alerts/{id} — remove alert

Frontend:
1. AlertConfig page — list of active alerts with enable/disable toggle
2. Form to add new alert: type selector, target search, threshold, webhook URL
3. Last triggered timestamp shown per alert
```

### Prompt 7: Operative Report (Hotspot Map)

```
You are working on Frontier Watch. Read CLAUDE.md first.

Build the Operative Report — server-wide hotspot intelligence.

Backend:
1. GET /api/hotspots — returns top 20 most active systems by kill count (24h)
   - Each system: name, kill_count_24h, kill_count_7d, trend (up/down/flat),
     controlling_corp, active_corps list, last_kill_timestamp
2. GET /api/activity/timeline — kill count per hour for last 24h (server-wide)
   Used for server activity graph
3. Background aggregation task — recomputes every 15 minutes

Activity prediction (Prism's +1/+2 hour feature):
- Simple: take same hour from last 7 days, compute average
- Return predicted_kills_1h, predicted_kills_2h per system
- This is a heuristic, label it as such in UI

Frontend:
1. OperativeReport page — full width
2. Top section: server activity graph (recharts AreaChart, last 24h)
3. Main section: sortable table of top 20 systems
   Columns: System | 24h Kills | 7d Kills | Trend | Controlling Corp | Last Activity
4. Click system row → navigate to SystemPage
5. Trend indicator: ↑ ↓ → colored green/red/grey
6. Refresh every 5 minutes automatically
```

---

## Build Order / Sprints

### Sprint 1: Foundation (Days 1–5)
**Goal:** Data flowing into SQLite, API responding

- [ ] Project scaffold (FastAPI, SQLite, React)
- [ ] Explore sandbox — discover real API endpoints and field names
- [ ] Database schema — all CREATE TABLE statements with real field names
- [ ] Poller skeleton — hits all endpoints, logs to stderr, never crashes
- [ ] Processor skeleton — normalizes into schema
- [ ] Health endpoint — GET /health returns uptime + row counts
- [ ] React shell — blank dashboard with nav, dark theme

**Done when:** `curl /health` returns data, poller is running, rows in SQLite.

### Sprint 2: Kill Feed (Days 6–10)
**Goal:** Live kill feed visible in browser

- [ ] Killmail ingestion — dedicated killmail.py if separate feed exists
- [ ] GET /api/killmails — paginated, filterable
- [ ] KillFeed React component — live polling, scrolling list
- [ ] Kill detail expand on click
- [ ] Basic filter bar (corp, system)
- [ ] Discord notifier.py — send test webhook

**Done when:** Kill feed shows live in browser with working filters.

### Sprint 3: System + Pilot Pages (Days 11–18)
**Goal:** Click a system or pilot — get intel

- [ ] System aggregation background task
- [ ] GET /api/systems/{id} — full system intel packet
- [ ] SystemPage component — 3 tabs (Activity / Fleets / Structures)
- [ ] Kill graph with recharts
- [ ] Pilot profile aggregation
- [ ] GET /api/pilots/{id}
- [ ] PilotPage component — stats, activity zones, ship preferences
- [ ] Top-nav search — FTS5 query, returns pilots/corps/systems

**Done when:** Can search any pilot or system and get meaningful intel.

### Sprint 4: LLM + Alerts (Days 19–24)
**Goal:** Automated intel delivery

- [ ] POST /api/intel/summary — Anthropic API integration
- [ ] IntelPanel component on SystemPage
- [ ] Alert evaluation loop
- [ ] GET/POST/DELETE /api/alerts
- [ ] AlertConfig UI page
- [ ] Discord webhook payload — formatted embeds with color coding
- [ ] Rate limiting on alerts (5-min cooldown per entity)

**Done when:** Can configure a corp watch → kill in system → Discord alert fires within 60s.

### Sprint 5: Operative Report + Polish (Days 25–31)
**Goal:** Hackathon-ready demo

- [ ] Hotspot aggregation — top 20 systems
- [ ] Activity prediction heuristic
- [ ] OperativeReport page
- [ ] Corp profile page (simplified from pilot page)
- [ ] Battle Report basic (multi-side kill reconstruction)
- [ ] Landing page / README for judges
- [ ] Demo video script
- [ ] Deploy to VPS

**Done when:** Full demo flow works end-to-end. Judges can run it themselves.

---

## Post-Hackathon Roadmap

| Phase | Feature | Priority |
|-------|---------|----------|
| 1 | Battle Report full (The Black Box) | High |
| 2 | Sui on-chain wallet flow integration | High |
| 3 | Corp profile page with PvP ratings | Medium |
| 4 | Fleet optimizer (composition vs threat data) | Medium |
| 5 | Public API for third-party builders | Low |
| 6 | Multi-region deployment + Postgres migration | Low |

---

## Key Design Decisions

**Why SQLite not Postgres:** Zero infrastructure complexity for a 3-week solo build. WAL mode handles concurrent reads during writes. FTS5 is built in. Migrate to Postgres when you have users.

**Why polling not WebSocket:** Simpler to implement, debug, and recover from failures. WebSocket upgrade path available in indexer.py when confirmed available from MUD Indexer.

**Why Discord not email/mobile:** Zero infrastructure. Every EVE player is already in Discord. Fastest path to real-time delivery without building a notification service.

**Why external app not Smart Assembly mod:** Broader audience (any player, not just assembly owners). Visual dashboard is easier to demo for hackathon judges. No Solidity/Move required for core value prop.

**Killmails as primary signal:** Coordinates are being hidden post-hackathon cycle. Killmails are the only durable positional data source long-term. Build everything around them.
