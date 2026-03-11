"""Tests for alert configuration endpoints."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_list_alerts_empty(client, tribe_with_leader):
    """List alerts returns empty list for new tribe."""
    _, headers = tribe_with_leader
    resp = await client.get("/alerts", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_alert(client, tribe_with_leader):
    """Can create a valid alert config."""
    _, headers = tribe_with_leader
    resp = await client.post(
        "/alerts",
        json={
            "alert_type": "kill_in_zone",
            "target_id": "zone-alpha-1",
            "target_name": "Alpha Sector",
            "threshold": 3,
            "discord_webhook_url": "https://discord.com/api/webhooks/123/abc",
            "cooldown_minutes": 10,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["alert_type"] == "kill_in_zone"
    assert data["target_id"] == "zone-alpha-1"
    assert data["target_name"] == "Alpha Sector"
    assert data["threshold"] == 3
    assert data["cooldown_minutes"] == 10
    assert data["enabled"] is True
    assert data["last_triggered"] is None


@pytest.mark.asyncio
async def test_create_alert_invalid_type(client, tribe_with_leader):
    """Invalid alert_type returns 422."""
    _, headers = tribe_with_leader
    resp = await client.post(
        "/alerts",
        json={
            "alert_type": "invalid_type",
            "discord_webhook_url": "https://discord.com/api/webhooks/123/abc",
        },
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_alert_invalid_webhook(client, tribe_with_leader):
    """Invalid webhook URL returns 422."""
    _, headers = tribe_with_leader
    resp = await client.post(
        "/alerts",
        json={
            "alert_type": "kill_in_zone",
            "discord_webhook_url": "https://evil.com/steal-token",
        },
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_alert_discordapp_webhook(client, tribe_with_leader):
    """discordapp.com webhook URL is also accepted."""
    _, headers = tribe_with_leader
    resp = await client.post(
        "/alerts",
        json={
            "alert_type": "corp_spotted",
            "discord_webhook_url": "https://discordapp.com/api/webhooks/456/def",
        },
        headers=headers,
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_update_alert_toggle(client, tribe_with_leader):
    """Can toggle alert enabled status."""
    _, headers = tribe_with_leader
    create_resp = await client.post(
        "/alerts",
        json={
            "alert_type": "hostile_scan",
            "discord_webhook_url": "https://discord.com/api/webhooks/123/abc",
        },
        headers=headers,
    )
    alert_id = create_resp.json()["id"]
    assert create_resp.json()["enabled"] is True

    # Disable
    resp = await client.patch(
        f"/alerts/{alert_id}",
        json={"enabled": False},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False

    # Re-enable
    resp = await client.patch(
        f"/alerts/{alert_id}",
        json={"enabled": True},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True


@pytest.mark.asyncio
async def test_delete_alert(client, tribe_with_leader):
    """Can delete own tribe's alert."""
    _, headers = tribe_with_leader
    create_resp = await client.post(
        "/alerts",
        json={
            "alert_type": "feral_evolved",
            "discord_webhook_url": "https://discord.com/api/webhooks/123/abc",
        },
        headers=headers,
    )
    alert_id = create_resp.json()["id"]

    resp = await client.delete(f"/alerts/{alert_id}", headers=headers)
    assert resp.status_code == 204

    # Verify gone
    list_resp = await client.get("/alerts", headers=headers)
    ids = [a["id"] for a in list_resp.json()]
    assert alert_id not in ids


@pytest.mark.asyncio
async def test_delete_alert_wrong_tribe(client, tribe_with_leader, second_auth_headers):
    """Deleting alert from different tribe returns 404."""
    _, leader_headers = tribe_with_leader

    # Create alert as tribe leader
    create_resp = await client.post(
        "/alerts",
        json={
            "alert_type": "blind_spot",
            "discord_webhook_url": "https://discord.com/api/webhooks/123/abc",
        },
        headers=leader_headers,
    )
    alert_id = create_resp.json()["id"]

    # Second user (no tribe) tries to delete — should get 400 (not in tribe)
    resp = await client.delete(f"/alerts/{alert_id}", headers=second_auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_test_alert_endpoint(client, tribe_with_leader):
    """Test alert endpoint attempts to send webhook."""
    _, headers = tribe_with_leader
    create_resp = await client.post(
        "/alerts",
        json={
            "alert_type": "clone_low",
            "discord_webhook_url": "https://discord.com/api/webhooks/123/abc",
        },
        headers=headers,
    )
    alert_id = create_resp.json()["id"]

    mock_response = AsyncMock()
    mock_response.status_code = 204

    with patch("app.modules.alerts.routes.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        resp = await client.post(f"/alerts/{alert_id}/test", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["sent"] is True
        assert data["status_code"] == 204


@pytest.mark.asyncio
async def test_list_alerts_no_tribe(client, auth_headers):
    """List alerts without tribe membership returns 400."""
    resp = await client.get("/alerts", headers=auth_headers)
    assert resp.status_code == 400
