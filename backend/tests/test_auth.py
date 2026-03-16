"""Auth route tests."""

from datetime import timedelta
from unittest.mock import patch

from app.auth.jwt import create_access_token


async def test_dev_login_creates_member(client):
    resp = await client.post("/auth/dev-login?name=Pilot1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["character_name"] == "Pilot1"
    assert data["wallet_address"].startswith("0x")
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_dev_login_returns_jwt(client):
    resp = await client.post("/auth/dev-login?name=JWTTest")
    token = resp.json()["access_token"]
    assert len(token) > 20  # Sanity check


async def test_dev_login_default_name(client):
    resp = await client.post("/auth/dev-login")
    assert resp.status_code == 200
    assert resp.json()["character_name"] == "DevPilot"


async def test_dev_login_disabled_in_production(client):
    with patch("app.auth.routes.settings") as mock_settings:
        mock_settings.environment = "production"
        resp = await client.post("/auth/dev-login?name=Hacker")
        assert resp.status_code == 403


async def test_unauthenticated_request_returns_401(client):
    resp = await client.get(
        "/census/tribes/00000000-0000-0000-0000-000000000001/members"
    )
    assert resp.status_code in (401, 403)


async def test_invalid_token_returns_401(client):
    resp = await client.get(
        "/census/tribes/00000000-0000-0000-0000-000000000001/members",
        headers={"Authorization": "Bearer garbage.token.here"},
    )
    assert resp.status_code == 401


async def test_expired_token_returns_401(client):
    token = create_access_token(
        {"sub": "0xdeadbeef", "name": "Expired"},
        expires_delta=timedelta(minutes=-1),
    )
    resp = await client.get(
        "/census/tribes/00000000-0000-0000-0000-000000000001/members",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


async def test_login_returns_501_without_credentials(client):
    """SSO login requires EVE_FRONTIER_CLIENT_ID to be configured."""
    resp = await client.get("/auth/login")
    assert resp.status_code == 501
    assert "SSO not configured" in resp.json()["detail"]


async def test_login_returns_authorize_url_with_credentials(client):
    with (
        patch("app.auth.routes.settings") as mock_route_settings,
        patch("app.auth.sso.settings") as mock_sso_settings,
    ):
        mock_route_settings.eve_frontier_client_id = "test-client-id"
        mock_sso_settings.eve_frontier_client_id = "test-client-id"
        mock_sso_settings.eve_frontier_callback_url = (
            "http://localhost:5173/auth/callback"
        )
        resp = await client.get("/auth/login", follow_redirects=False)
        assert resp.status_code == 307
        location = resp.headers["location"]
        assert "auth.evefrontier.com" in location
        assert "test-client-id" in location
