# Gap Analysis: Spec vs Current Code
> Generated: March 10, 2026 | Pre-hackathon prep

## MODULE 1: CENSUS — 90% Complete

| Feature | Status | Notes |
|---------|--------|-------|
| SSO / wallet login | ✅ Done | FusionAuth + dev-login |
| Member roster with roles | ✅ Done | leader/officer/member/recruit |
| Join request queue | ✅ Done | approve/deny workflow |
| Invite code onboarding | ✅ Done | 32-char codes |
| World API sync | ✅ Done | /sync/tribes, /sync/tribes/{id}/members |
| Member activity (last_active) | ⚠️ Partial | Field exists, not updated on API calls |
| Primary ship class field | ❌ Missing | Spec calls for it, easy column add |
| Active/inactive status | ❌ Missing | Derived from last_active, needs logic |

**Action items:**
- Add `ship_class` column to Member model
- Add middleware to update `last_active` on authenticated requests
- Add active/inactive derived field to MemberResponse (>7 days = inactive)

## MODULE 2: FORGE PLANNER — 85% Complete

| Feature | Status | Notes |
|---------|--------|-------|
| Job CRUD | ✅ Done | Create, assign, update, delete |
| Status flow (queued→complete) | ✅ Done | 4 statuses with validation |
| Tribe inventory | ✅ Done | Upsert with unique constraint |
| Blueprint search (World API) | ⚠️ Partial | Has static fallback data |
| Gap analysis endpoint | ❌ Missing | Required vs held, key differentiator |
| Kanban UI | ✅ Done | 4-column board |
| In-app notifications | ❌ Missing | Spec says "not email for now" |

**Action items:**
- Build `GET /forge/tribes/{id}/gap-analysis` — compare job materials vs inventory
- Add bill-of-materials data (static JSON or World API)
- Add notification model + simple in-app feed

## MODULE 3: LEDGER — 80% Complete

| Feature | Status | Notes |
|---------|--------|-------|
| Sui wallet balances | ✅ Done | suix_getAllBalances |
| Transaction history | ✅ Done | Record + display |
| Token contract connect | ✅ Done | tribe.token_contract_address |
| Allocation tool (send tokens) | ❌ Missing | Requires Sui signing — read-only for now |
| Treasury summary endpoint | ❌ Missing | total supply, in circulation, held by leadership |

**Action items:**
- Build `GET /ledger/tribes/{id}/summary` — aggregate balances
- Allocation tool is stretch (requires wallet signing client-side)

## C5 FEATURES (FRONTIER_WATCH_C5_TASKS) — 0% Complete

All net-new:
- [ ] Cycle field on existing tables
- [ ] Orbital zones + feral AI tracking
- [ ] Void scanning intel feed
- [ ] Clone manufacturing status
- [ ] Crown/identity system
- [ ] 5 Discord alert types
- [ ] 5 new frontend panels

## PRE-HACKATHON CHECKLIST

| Item | Status |
|------|--------|
| GitHub repo created | ✅ |
| Backend scaffolded (FastAPI + SQLAlchemy) | ✅ |
| Frontend scaffolded (React + Tailwind) | ✅ |
| docker-compose local dev | ✅ |
| CI pipeline | ✅ |
| Deploy to Fly.io | ✅ |
| Deploy frontend to Vercel | ✅ |
| Security hardened | ✅ |
| 103 backend tests | ✅ |
| Register at deepsurge.xyz | ❓ User action |
| Read builder docs | ❓ User action |
| Join builder Discord | ❓ User action |
| Confirm live World API endpoints | 🔲 TODO |

## PRIORITY ORDER (Hackathon Impact)

1. **Last_active middleware** — Quick win, shows liveness
2. **Gap analysis endpoint** — Key differentiator vs EF-Map
3. **Treasury summary** — Judges love dashboard numbers
4. **C5 schema migration** — Foundation for Week 1 features
5. **Active/inactive status** — Community vote appeal
6. **Ship class field** — Minor polish
