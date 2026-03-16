# Changelog

All notable changes to Frontier Tribe OS will be documented in this file.

## [0.1.0] - 2026-03-16

### Added
- **Census**: EVE Frontier SSO (FusionAuth), member roster, role hierarchy (Leader/Officer/Member/Recruit), invite-code join flow
- **Forge**: Production job board (Kanban), tribe inventory, blueprint picker, gap analysis
- **Ledger**: Sui wallet balances via JSON-RPC, transaction history, treasury summary, @mysten/dapp-kit wallet connect
- **Watch**: C5 orbital zone monitoring, signature resolution, feral AI tracking, clone status, crown roster
- **Intel**: Kill feed with global search, pilot/corp profiles, battle reports, LLM-powered FC briefings (Claude Haiku)
- **Alerts**: Discord webhook notifications, 6 alert types with per-entity cooldowns, blind spot detection
- **Warden**: Move contract threat hypothesis engine with automated security evaluation cycles
- Rate limiting on all API endpoints (slowapi)
- Structured JSON logging with request ID correlation
- HSTS, CSP, Permissions-Policy security headers
- Global exception handler with consistent error schema
- Frontend 404 catch-all page
- CI/CD: lint, test, security scan, deploy automation (Fly.io + Vercel)
- 193 backend tests, TypeScript strict mode frontend
- World API poller for tribe/killmail sync
- Demo seed script for hackathon presentations
