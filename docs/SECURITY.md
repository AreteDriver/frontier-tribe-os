# Security Policy — Aegis Stack

## Projects Covered

| Project | Type | Risk Level |
|---|---|---|
| Frontier Watch | Operational intelligence dashboard | High |
| The Black Box | Forensic engine (blockchain data) | High |
| The Sovereign | On-chain governance contracts | Critical |
| The Silk Road Protocol | Autonomous trade contracts | Critical |
| The Warden System | Autonomous defense contracts | Critical |

---

## Reporting a Vulnerability

This is a hackathon submission. If you discover a vulnerability during the EVE Frontier × Sui Hackathon 2026 evaluation period, contact the maintainer directly before public disclosure.

**Do not open a public GitHub issue for security vulnerabilities.**

---

## Threat Surface by Layer

### Layer 1: Smart Contracts (Move / Sui)

All on-chain logic is written in Move and deployed to the Sui blockchain.

**Known risk areas:**
- Object ownership and capability management (Sovereign, Warden, Silk Road)
- Access control on privileged entry functions
- Atomic transaction abuse in trade contract execution (Silk Road)

**Mitigations in place:**
- All privileged functions assert sender authorization via `assert!(ctx.sender() == authorized, ENotAuthorized)`
- `AdminCap` objects are stored in transfer-locked structures — never in shared mutable state
- Adversarial test suite covers ownership confusion and unauthorized invocation scenarios
- Contracts reviewed against Movebit and OtterSec Move security checklists

### Layer 2: Backend / API Services

**Known risk areas:**
- EVE ESI OAuth token handling (Frontier Watch, Black Box)
- Sui RPC endpoint exposure
- Database query construction

**Mitigations in place:**
- All secrets loaded from environment variables — never hardcoded
- ESI tokens stored server-side only, never sent to frontend
- Sui RPC calls proxied through backend — raw RPC endpoint not exposed
- Parameterized queries only — no string interpolation in DB calls

### Layer 3: Frontend (Frontier Watch Dashboard)

**Known risk areas:**
- XSS via EVE Online character/corp/item name rendering
- CORS misconfiguration
- Unvalidated on-chain string rendering

**Mitigations in place:**
- All EVE ESI data rendered as text nodes — `dangerouslySetInnerHTML` prohibited
- DOMPurify applied before any HTML rendering
- Content Security Policy headers enforced
- CORS whitelist applied — `Access-Control-Allow-Origin: *` explicitly prohibited

---

## Secrets Management

See `docs/SECRETS.md` for full protocol.

**Rules:**
- `.env` is gitignored — `.env.example` is the committed reference
- Private keys never appear in source or logs
- Rotate any key that touches a public repo immediately
- CI/CD secrets stored in GitHub Actions encrypted secrets — never in workflow files

---

## Dependency Policy

- Dependencies pinned to exact versions in production builds
- `npm audit` and `cargo audit` run before each deployment
- No unvetted dependencies with filesystem or network access in contract-adjacent code

---

## Security Checklist (Pre-Submission)

- [ ] `.gitignore` covers all `.env` files across all packages
- [ ] No private keys, API keys, or tokens in git history (`git log -p | grep -i "key\|secret\|token"`)
- [ ] All Move entry functions have explicit access control assertions
- [ ] `AdminCap` transfer path reviewed and locked
- [ ] Frontier Watch frontend has CSP headers active
- [ ] ESI token refresh logic does not log token values
- [ ] Sui RPC not directly exposed to browser
- [ ] `npm audit` passes with no critical findings
- [ ] Adversarial Move test suite passes

---

## Key Rotation Procedure

If a secret is compromised or accidentally exposed:

1. **Immediately rotate** — generate a new key/token at the source (Anthropic console, EVE dev portal, etc.)
2. **Revoke the old credential** — do not wait
3. **Audit git history** — `git log -p | grep <partial_key>` to confirm scope of exposure
4. **Check for unauthorized usage** — review API logs if available
5. **Update all deployment environments** with new credential
6. **Document the incident** in `docs/INCIDENT_LOG.md`

---

## Contact

Maintainer: ARETE (AreteDriver)
GitHub: github.com/AreteDriver
