# Frontier Tribe OS — Move Smart Contracts

On-chain modules for the Frontier Tribe OS platform (EVE Frontier x Sui Hackathon 2026).

## Package Structure

### `contracts/` (aegis_stack)

The root package contains the core Aegis protocol modules:

- **admin.move** — AdminCap capability and emergency pause controls
- **errors.move** — Shared named error constants across all modules
- **sovereign.move** — Governance proposals with timelock and vote-weight protection
- **silk_road.move** — Trade escrow with flag-before-transfer and anti-wash-trade
- **warden.move** — Basic autonomous defense config (cooldown, value caps)

### `contracts/warden/` (warden)

Dedicated Warden defense package with full tribe defense and identity features:

- **warden.move** — Core defense module:
  - `TribeRegistry` — shared object with defense and gate policies per tribe
  - `DefensePolicy` — auto-lock tiers, alert thresholds, cooldown, response caps
  - `GatePolicy` — whitelist/blacklist gate access control
  - `ThreatReport` — event emitted on threat detection (auto-locks gate if tier exceeds policy)
  - `AdminCap` — capability for config mutations (owned, never shared)

- **crown.move** — Crown NFT identity tokens:
  - `Crown` — NFT with type classification, encoded memories, and mint timestamp
  - `weave_crown()` — mint a Crown NFT to the caller
  - `transfer_crown()` — transfer to another player
  - `burn_crown()` — permanently destroy a Crown

## Security Model

All contracts follow the hardening rules documented in `docs/MOVE_HARDENING.md`:

- **AdminCap never in shared objects** — transferred to deployer at init
- **Checks-then-acts** — all assertions before state mutations
- **Flag-before-effects** — state flags set before asset transfers or events
- **Named error constants** — no magic numbers in abort codes
- **Emergency pause** — circuit breaker on all state-mutating operations

## Build

```bash
# Build the aegis_stack package
cd contracts/
sui move build

# Build the warden package
cd contracts/warden/
sui move build
```

## Test

```bash
# Test aegis_stack
cd contracts/
sui move test

# Test warden
cd contracts/warden/
sui move test
```

## Deploy

```bash
# Deploy to testnet (requires funded wallet)
sui client publish --gas-budget 100000000

# Deploy warden package
cd contracts/warden/
sui client publish --gas-budget 100000000
```

## Hackathon Note

This is a hackathon scaffold for the EVE Frontier x Sui Hackathon 2026 (March 11-31).
Production deployment would require:

- Full security audit by a Move auditing firm
- Adversarial test coverage for every privileged entry function
- Gas profiling under realistic load
- Timelock / multisig on AdminCap for production governance
- Review against the [MoveBit security checklist](https://github.com/movebit/movescan-security-checklist)
