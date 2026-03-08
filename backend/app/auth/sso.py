"""EVE Frontier SSO OAuth2 flow.

NOTE: EVE Frontier auth may be wallet-based (Sui) rather than traditional OAuth2.
This module is a placeholder that will be updated once we verify the actual auth mechanism
from the builder docs / Discord.

For hackathon dev: we include a dev-mode bypass that creates a mock identity,
so Census UI can be built before SSO is confirmed.
"""

import secrets

import httpx

from app.config import settings

# Placeholder — update once we verify EVE Frontier's actual SSO endpoints
SSO_AUTHORIZE_URL = "https://auth.evefrontier.com/oauth2/authorize"
SSO_TOKEN_URL = "https://auth.evefrontier.com/oauth2/token"
SSO_VERIFY_URL = "https://auth.evefrontier.com/oauth2/verify"


async def get_authorize_url(state: str | None = None) -> str:
    """Build the SSO authorization redirect URL."""
    state = state or secrets.token_urlsafe(32)
    params = {
        "response_type": "code",
        "client_id": settings.eve_frontier_client_id,
        "redirect_uri": settings.eve_frontier_callback_url,
        "scope": "publicData",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{SSO_AUTHORIZE_URL}?{query}", state


async def exchange_code(code: str) -> dict:
    """Exchange authorization code for access token."""
    async with httpx.AsyncClient() as client:
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


async def verify_token(access_token: str) -> dict:
    """Verify access token and get character info."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            SSO_VERIFY_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


def generate_dev_identity(name: str = "DevPilot") -> dict:
    """Generate a mock identity for development without SSO."""
    return {
        "character_id": f"dev-{secrets.token_hex(8)}",
        "character_name": name,
    }
