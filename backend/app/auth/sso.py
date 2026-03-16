"""EVE Frontier auth via FusionAuth OAuth2 + Sui zkLogin.

Auth flow:
1. User clicks Login → redirect to FusionAuth OAuth2 authorize endpoint
2. User authenticates (email/password, Google, Twitch, Facebook)
3. FusionAuth redirects back with authorization code
4. We exchange code for access token + ID token
5. ID token contains user info; wallet address is derived via zkLogin/Enoki
6. We issue our own JWT for session management

The FusionAuth OAuth2 endpoint is at auth.evefrontier.com.
Registration: auth.evefrontier.com/oauth2/register

For hackathon dev: dev-mode bypass creates mock identities so Census UI
can be built before SSO client credentials are obtained.
"""

import secrets

import httpx

from app.config import settings

# EVE Frontier FusionAuth OAuth2 endpoints
SSO_AUTHORIZE_URL = "https://auth.evefrontier.com/oauth2/authorize"
SSO_TOKEN_URL = "https://auth.evefrontier.com/oauth2/token"
SSO_USERINFO_URL = "https://auth.evefrontier.com/oauth2/userinfo"

# World API for character lookups
WORLD_API_BASE = "https://blockchain-gateway-stillness.live.tech.evefrontier.com"


async def get_authorize_url(state: str | None = None) -> tuple[str, str]:
    """Build the FusionAuth OAuth2 authorization redirect URL."""
    state = state or secrets.token_urlsafe(32)
    params = {
        "response_type": "code",
        "client_id": settings.eve_frontier_client_id,
        "redirect_uri": settings.eve_frontier_callback_url,
        "scope": "openid profile email",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{SSO_AUTHORIZE_URL}?{query}", state


async def exchange_code(code: str) -> dict:
    """Exchange authorization code for access + ID tokens."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            SSO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.eve_frontier_callback_url,
                "client_id": settings.eve_frontier_client_id,
                "client_secret": settings.eve_frontier_client_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_userinfo(access_token: str) -> dict:
    """Get user info from FusionAuth userinfo endpoint."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            SSO_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def get_smart_character(wallet_address: str) -> dict | None:
    """Lookup smart character from World API by wallet address."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{WORLD_API_BASE}/v2/smartcharacters/{wallet_address}"
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError:
        return None


def generate_dev_identity(name: str = "DevPilot") -> dict:
    """Generate a mock identity for development without SSO."""
    return {
        "wallet_address": f"0x{secrets.token_hex(20)}",
        "character_name": name,
    }
