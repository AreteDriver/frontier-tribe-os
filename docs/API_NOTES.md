# EVE Frontier World API Notes

## Base URL (Stillness Server)
```
https://blockchain-gateway-stillness.live.tech.evefrontier.com
```

**Swagger UI**: https://blockchain-gateway-stillness.live.tech.evefrontier.com/docs/index.html
**OpenAPI Spec**: https://blockchain-gateway-stillness.live.tech.evefrontier.com/docs/doc.json

## Authentication

**EVE Frontier does NOT use EVE Online's OAuth2 SSO.**

Auth is built on **Sui blockchain zkLogin** via **EVE Vault** (Chrome extension + web wallet):
- OAuth2 endpoint: `https://auth.evefrontier.com/oauth2/authorize` (FusionAuth, not CCP)
- Identity derived via Mysten Labs' Enoki API (zkLogin zero-knowledge proofs)
- Supported login: Email/password, Google, Twitch, Facebook
- Wallet address is cryptographically derived from OAuth identity
- Sponsored gas fees — players don't need SUI tokens

**API Auth**: BearerAuth (API key in `Authorization` header). Most endpoints are public.

## Endpoints (v0.1.38)

### Public (No Auth)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service status |
| GET | `/config` | Chain connection config |
| GET | `/v2/smartcharacters` | All characters, paginated |
| GET | `/v2/smartcharacters/{address}` | Character by wallet address |
| GET | `/v2/smartassemblies` | All assemblies (filter: SmartStorageUnit, SmartGate, SmartTurret) |
| GET | `/v2/smartassemblies/{id}` | Single assembly |
| GET | `/v2/killmails` | All killmails, paginated (limit 0-100) |
| GET | `/v2/killmails/{id}` | Single killmail |
| GET | `/v2/tribes` | All tribes (limit 0-1000) |
| GET | `/v2/tribes/{id}` | Single tribe |
| GET | `/v2/types` | All game types (limit 0-1000) |
| GET | `/v2/types/{id}` | Single game type |
| GET | `/v2/solarsystems` | All solar systems (limit 0-1000) |
| GET | `/v2/solarsystems/{id}` | Single solar system |
| GET | `/v2/fuels` | Assembly fuel data |

### Authenticated (BearerAuth)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v2/smartcharacters/me/jumps` | Current user's gate jumps |
| GET | `/v2/smartcharacters/me/jumps/{id}` | Single jump |

## Key Concepts

- **Smart Characters**: Player identities tied to Sui wallet addresses (soul-bound)
- **Smart Assemblies**: Player-built on-chain structures (gates, turrets, storage)
- **Tribes**: Player organizations/corps — THIS IS WHAT WE BUILD ON
- **Types**: Game item/object definitions — materials, blueprints
- **PODs**: Provable Object Datatypes — ZK-verifiable signed data objects

## Tribe OS Integration Plan

### Census Module
- `GET /v2/tribes` — List all tribes (verify member data structure)
- `GET /v2/tribes/{id}` — Get tribe details + member list
- `GET /v2/smartcharacters/{address}` — Player profile by wallet address
- Auth: Use FusionAuth OAuth2 flow → derive wallet → JWT

### Forge Module
- `GET /v2/types` — Item/blueprint type definitions for BOM
- `GET /v2/smartassemblies` — Track tribe's deployed assemblies

### Ledger Module
- Read Sui on-chain token balances directly via Sui SDK (not World API)
- Use wallet address from smart character data

## C5 Changes (March 2026)

### Chain Migration: Ethereum → Sui
EVE Frontier moved from Ethereum to Sui blockchain. All on-chain data now uses
Sui addresses and transaction formats. Our Sui SDK integration is correct.

### Location Obfuscation
Structure locations are now **hidden on-chain by default** — only readable as a
hash. This means:
- `coordinates` fields store hashes, not plaintext x/y/z
- Raw positions are NOT available from chain reads
- Future: "selective data secrecy, information trading" — potential API for
  authorized coordinate reveals
- Our `OrbitalZone.coordinates_hash` field reflects this

**Impact on Tribe OS**: We cannot build a map from on-chain data alone.
Zone names and threat levels are still useful. If CCP releases a coordinate
reveal API, we can integrate it later.

## Static Data Fallback

If World API is unavailable, load from `backend/data/blueprints.json`.

## Builder Resources

- Builder Docs: https://docs.evefrontier.com
- DApp Development: https://docs.evefrontier.com/Dapp
- Smart Contracts: https://docs.evefrontier.com/smart
- Whitepaper: https://whitepaper.evefrontier.com/technology
- Hackathon: https://www.deepsurge.xyz/evefrontier2026
