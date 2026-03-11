# Frontier Tribe OS -- Demo Script

> 3-minute walkthrough for EVE Frontier x Sui Hackathon 2026 judges.
> Target: show all four modules in action with real data flows.

## Setup Before Recording

- Frontend running: https://frontend-ten-theta-80.vercel.app
- API docs visible: https://frontier-tribe-os.fly.dev/docs
- Discord webhook configured for alert demo
- Two browser windows ready (main + incognito for join flow)
- Pre-create one orbital zone and a few scans for Watch feed

---

## 1. Landing Page and Authentication (20s)

1. Open the landing page -- show the project title and module overview.
2. Click **Login** (Dev Login for demo, or FusionAuth SSO if configured).
3. Redirected to the Dashboard.

**Narration**: "Frontier Tribe OS authenticates via EVE Frontier's FusionAuth SSO with Sui zkLogin. For this demo, we use dev-login to skip the OAuth flow."

---

## 2. Dashboard -- Summary Cards (20s)

1. Show the dashboard with summary cards:
   - Active production jobs count
   - Treasury balance (from Sui JSON-RPC)
   - Active alerts count
   - Member count
2. Point out the cycle banner: "CYCLE 5 // SHROUD OF FEAR // DAY N"

**Narration**: "The dashboard gives tribe leaders a single view of operations -- who is here, what is being built, where the money is, and what threats are active."

---

## 3. Census -- Member Roster (30s)

1. Navigate to **Roster**.
2. Show the member list with role badges (Leader, Officer, Member, Recruit).
3. Show activity status (last active timestamp).
4. Copy the tribe **invite code**.
5. In incognito window: dev-login as a second pilot, paste invite code, submit join request.
6. Back in main window: approve the join request.
7. Roster updates to show the new member.

**Narration**: "Census manages the tribe roster. Leaders control who joins through an invite-code flow with approval. Roles enforce access across all modules."

---

## 4. Forge -- Production Planning with Gap Analysis (40s)

1. Navigate to **Forge Planner**.
2. Click **Create Job** -- pick a blueprint from the dropdown, set quantity.
3. Job appears in the **Queued** column.
4. Move job to **In Progress** (click or drag).
5. Show the tribe **Inventory** -- add some materials.
6. Open **Gap Analysis** -- show the material deficit view:
   - Required materials for active jobs
   - Current tribe inventory
   - Deficit (what is missing)
7. Mark materials as ready on a job.

**Narration**: "Forge is the production ops layer. It answers the question every tribe leader asks: who is building what, and what is blocking them. The gap analysis shows material deficits across all active jobs against tribe inventory."

---

## 5. Ledger -- Treasury and Wallets (30s)

1. Navigate to **Ledger**.
2. Show **Treasury Summary** -- balance pulled live from Sui JSON-RPC.
3. Show **Member Wallets** -- individual balances per member.
4. Show **Transaction History** with on-chain `tx_digest` links.
5. Highlight non-custodial design: "Backend reads balances but never holds keys."

**Narration**: "Ledger reads real Sui wallet balances via JSON-RPC. It is fully non-custodial -- the backend records transactions but all signing happens client-side through dapp-kit. No private keys ever touch the server."

---

## 6. Watch -- Threat Intel and Signature Resolution (40s)

1. Navigate to **Watch**.
2. Show the **Orbital Zone** list sorted by threat level (DORMANT > ACTIVE > EVOLVED > CRITICAL).
3. Create a new orbital zone (name, zone ID).
4. **Submit a scan**:
   - Select the zone
   - Set result type: HOSTILE
   - Set signature type: EM
   - Slide the **resolution** to 60% -- label shows "IDENTIFIED"
   - Slide to 20% -- label changes to "UNRESOLVED"
   - Set to 80% -- "FULL_INTEL"
   - Submit at 80%
5. Show the **Scan Feed** -- newest scan appears at top with:
   - Result type badge (HOSTILE)
   - Signature type (EM)
   - Resolution label (FULL_INTEL)
   - Confidence percentage
6. Show **Blind Spots** -- any zone not scanned in 20+ minutes is flagged.
7. Show clone reserves and crown roster panels.

**Narration**: "Watch is our C5 threat intel module. The Signature Resolution System uses graduated detection -- scans go from UNRESOLVED through PARTIAL and IDENTIFIED to FULL_INTEL, matching EVE Frontier's passive observation mechanics. Four signature types: EM, HEAT, GRAVIMETRIC, RADAR. Zones not scanned in 20 minutes are flagged as blind spots."

---

## 7. Discord Alert Fires (20s)

1. Show the Discord channel.
2. Point to the alert that fired when the HOSTILE scan was submitted:
   - "HOSTILE DETECTED -- [Zone Name] scan by [Character]"
3. Mention other alert types:
   - Feral AI evolution
   - Blind spot warnings
   - Low clone reserve

**Narration**: "Every hostile scan, AI evolution event, and blind spot triggers a Discord webhook alert. Tribe leaders get notified without polling the dashboard."

---

## Closing (10s)

**Narration**: "Frontier Tribe OS -- four modules, one platform. Census for identity, Forge for production, Ledger for treasury, Watch for threat intel. 136 tests, deployed on Fly.io and Vercel, non-custodial Sui integration, and zero competition in the EVE Frontier ecosystem. Built solo by AreteDriver."

---

## Talking Points (if judges ask questions)

- **Why four modules?** Tribes need coordination across identity, production, finance, and security. A tool that only does one is just another spreadsheet.
- **Why non-custodial?** Trust is earned in EVE. No tribe leader will hand private keys to a third-party tool. Read-only chain access with client-side signing is the only credible design.
- **What is the Signature Resolution System?** EVE Frontier C5 introduces passive observation. You do not get perfect intel instantly -- you get graduated visibility based on scan quality. Our system models this with four resolution tiers and four signature types.
- **What about the World API?** We poll the blockchain gateway for tribe, character, and killmail data. Static JSON fallback if the API is unavailable. Document all findings in API_NOTES.md.
- **Post-hackathon?** SaaS model. Free tier (1 tribe, 10 members, Census only). Tribe Pro at $15/mo. Syndicate tier at $49/mo for multi-tribe management.
