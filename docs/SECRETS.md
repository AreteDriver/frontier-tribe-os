# Secrets Management Guide — Aegis Stack

## The Core Problem

Hackathons move fast. Fast = `.env` files accidentally committed, API keys hardcoded "just for testing," tokens pasted into Discord for debugging. Any of these in a public repo means your credentials are compromised — often within minutes, by automated scanners.

This guide gives you a system that keeps you fast without burning your keys.

---

## Secrets Inventory

Know what you're protecting:

| Secret | Used By | Risk if Exposed |
|---|---|---|
| `SUI_DEPLOYER_PRIVATE_KEY` | Contract deployment scripts | Attacker can deploy, upgrade, or drain contracts |
| `SUI_ADMIN_PRIVATE_KEY` | AdminCap operations | Full protocol control |
| `EVE_ESI_CLIENT_ID` | Frontier Watch OAuth | Low alone — needs client secret too |
| `EVE_ESI_CLIENT_SECRET` | Frontier Watch OAuth | Can impersonate your app, access user data |
| `EVE_ESI_ACCESS_TOKEN` | ESI API calls | Can query/act as authenticated user |
| `ANTHROPIC_API_KEY` | Animus/AI integrations | Billed to your account, prompt injection risk |
| `DATABASE_URL` | Backend services | Full DB read/write access |
| `JWT_SECRET` | Session signing | Session hijacking across all users |

---

## Step 1: .env Structure

### Root monorepo structure

```
aegis-stack/
├── .env                    # GITIGNORED — your actual secrets
├── .env.example            # COMMITTED — template with empty values
├── .gitignore
├── frontier-watch/
│   ├── .env                # GITIGNORED
│   └── .env.example        # COMMITTED
├── contracts/
│   ├── .env                # GITIGNORED — deployer keys
│   └── .env.example        # COMMITTED
```

### Root `.env.example` (commit this)

```bash
# Sui Network
SUI_NETWORK=mainnet
SUI_RPC_URL=https://fullnode.mainnet.sui.io

# Contract Deployment (NEVER commit actual keys)
SUI_DEPLOYER_PRIVATE_KEY=
SUI_ADMIN_PRIVATE_KEY=

# EVE ESI OAuth
EVE_ESI_CLIENT_ID=
EVE_ESI_CLIENT_SECRET=
EVE_ESI_REDIRECT_URI=http://localhost:3000/auth/callback

# Database
DATABASE_URL=

# Application
JWT_SECRET=
NODE_ENV=development
PORT=3000

# AI Services
ANTHROPIC_API_KEY=
```

### Root `.gitignore` (critical entries)

```gitignore
# Secrets — never commit
.env
.env.local
.env.production
.env.*.local
*.pem
*.key
*.p12

# Sui keystore
sui.keystore
sui_config/

# Common accidental exposure
.DS_Store
*.log
```

---

## Step 2: Verify Nothing Is Already Exposed

Run this before you push anything:

```bash
# Scan git history for common secret patterns
git log -p | grep -iE "(private_key|api_key|secret|password|token)" | head -50

# Check if .env is tracked
git ls-files | grep .env

# Check current working tree for secrets
grep -r "ANTHROPIC\|SUI_DEPLOYER\|ESI_SECRET" --include="*.ts" --include="*.js" --include="*.py" . \
  | grep -v ".env.example" \
  | grep -v "process.env"
```

If `.env` appears in `git ls-files`, it's tracked. Fix immediately:

```bash
git rm --cached .env
echo ".env" >> .gitignore
git commit -m "remove .env from tracking"
```

**This does not remove it from history.** If it was ever pushed public, rotate the keys.

---

## Step 3: Removing Secrets From Git History

If keys were committed to a public repo, rotation is mandatory. History scrubbing is secondary (do both):

### Rotate first (always)
Go to each service and generate new credentials:
- Sui: `sui keytool generate ed25519` for new keypairs
- Anthropic: console.anthropic.com → API Keys → rotate
- EVE ESI: developers.eveonline.com → your app → regenerate secret

### Then scrub history (if needed)

```bash
# Install BFG Repo Cleaner (faster than git filter-branch)
# https://rtyley.github.io/bfg-repo-cleaner/

# Create a file listing the secrets to remove
echo "your-exposed-api-key-here" > secrets.txt

# Run BFG against your repo
java -jar bfg.jar --replace-text secrets.txt your-repo.git

# Force push (coordinate with team first)
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

---

## Step 4: Loading Secrets in Code

### Node.js / TypeScript (Frontier Watch backend)

```typescript
import 'dotenv/config'; // load .env at startup

// Validate required secrets exist at startup — fail fast
function requireEnv(key: string): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
}

// Export validated config — never access process.env directly elsewhere
export const config = {
  sui: {
    network: requireEnv('SUI_NETWORK'),
    rpcUrl: requireEnv('SUI_RPC_URL'),
  },
  esi: {
    clientId: requireEnv('EVE_ESI_CLIENT_ID'),
    clientSecret: requireEnv('EVE_ESI_CLIENT_SECRET'),
    redirectUri: requireEnv('EVE_ESI_REDIRECT_URI'),
  },
  db: {
    url: requireEnv('DATABASE_URL'),
  },
  jwt: {
    secret: requireEnv('JWT_SECRET'),
  },
} as const;
```

**Why `requireEnv`:** If you deploy without setting an env var, it fails immediately at startup with a clear error — not silently at runtime when a user tries to log in.

### Python (if used in Animus integrations)

```python
import os
from dotenv import load_dotenv

load_dotenv()

def require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value

config = {
    "anthropic_api_key": require_env("ANTHROPIC_API_KEY"),
    "database_url": require_env("DATABASE_URL"),
}
```

### Sui CLI / deployment scripts

```bash
#!/bin/bash
# deploy.sh

set -e  # exit on any error

# Load from .env if present
if [ -f .env ]; then
  export $(cat .env | grep -v '#' | xargs)
fi

# Validate required vars
: "${SUI_DEPLOYER_PRIVATE_KEY:?SUI_DEPLOYER_PRIVATE_KEY is required}"
: "${SUI_NETWORK:?SUI_NETWORK is required}"

# Import key for deployment (do not store in sui.keystore in repo)
echo "$SUI_DEPLOYER_PRIVATE_KEY" | sui keytool import --key-scheme ed25519

sui client publish --gas-budget 100000000
```

---

## Step 5: GitHub Actions (CI/CD)

Store secrets in GitHub repository settings, not in workflow files.

**Settings → Secrets and variables → Actions → New repository secret**

```yaml
# .github/workflows/deploy.yml
name: Deploy Contracts

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Sui
        env:
          SUI_DEPLOYER_PRIVATE_KEY: ${{ secrets.SUI_DEPLOYER_PRIVATE_KEY }}
          SUI_NETWORK: ${{ secrets.SUI_NETWORK }}
        run: ./scripts/deploy.sh
```

**Never do:**
```yaml
env:
  SUI_DEPLOYER_PRIVATE_KEY: "0xabcd1234..."  # exposed in repo and logs
```

---

## Step 6: Secret Scanning (Automated Protection)

### Enable GitHub Secret Scanning

Repository → Settings → Security → Secret scanning → Enable

This automatically alerts you if a known secret pattern (API keys, private keys) is detected in a push.

### Add pre-commit hook (local protection)

```bash
# Install detect-secrets
pip install detect-secrets --break-system-packages

# Create baseline (documents known false positives)
detect-secrets scan > .secrets.baseline

# Add pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
detect-secrets-hook --baseline .secrets.baseline
if [ $? -ne 0 ]; then
  echo "Potential secret detected. Review before committing."
  exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

Now every commit is scanned locally before it leaves your machine.

---

## Emergency: Key Compromised

If you believe a secret is exposed:

```
1. ROTATE IMMEDIATELY — do not investigate first, rotate first
2. Check API logs for unauthorized usage (Anthropic console, EVE dev portal)
3. Scrub git history if repo is public (BFG)
4. Update all environments (local, CI, any deployed instances)
5. Log the incident: what was exposed, when, what was rotated
```

Time matters. Automated scanners harvest GitHub commits within seconds of a push.

---

## Pre-Submission Secrets Checklist

- [ ] `git ls-files | grep .env` returns nothing
- [ ] `.env.example` committed with all keys present but values empty
- [ ] `git log -p | grep -iE "private_key|api_key|secret"` returns no actual values
- [ ] GitHub Secret Scanning enabled on all public repos
- [ ] `detect-secrets` pre-commit hook active
- [ ] All GitHub Actions secrets stored in repo settings, not workflow files
- [ ] `requireEnv` / equivalent used — app fails fast if secrets missing
- [ ] Sui keypairs not in `sui.keystore` within repo directory
- [ ] ESI client secret confirmed absent from frontend bundle
- [ ] JWT_SECRET is a randomly generated 256-bit value, not a word or phrase
