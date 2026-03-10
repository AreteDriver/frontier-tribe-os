#!/bin/bash
# Deploy Aegis Stack contracts to Sui.
# Reads deployer key from .env — never hardcode.
# See docs/SECRETS.md "Sui CLI / deployment scripts"

set -euo pipefail

# Load .env if present
if [ -f .env ]; then
    export $(grep -v '#' .env | xargs)
fi

# Validate required vars — fail fast
: "${SUI_DEPLOYER_PRIVATE_KEY:?SUI_DEPLOYER_PRIVATE_KEY is required — set in .env}"
: "${SUI_NETWORK:=mainnet}"

echo "Deploying Aegis Stack to ${SUI_NETWORK}..."

# Import key for deployment (ephemeral — do not persist in sui.keystore in repo)
echo "${SUI_DEPLOYER_PRIVATE_KEY}" | sui keytool import --key-scheme ed25519

sui client publish --gas-budget 100000000

echo "Deploy complete."
