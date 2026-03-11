"""Tests for Watch alert endpoints."""

import pytest


@pytest.mark.asyncio
async def test_blind_spots_empty(client, auth_headers):
    """No zones means no blind spots."""
    resp = await client.get("/watch/alerts/blind-spots", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["blind_spots"] == []


@pytest.mark.asyncio
async def test_blind_spots_with_unscanned_zone(client, auth_headers):
    """Zone with no scans shows as blind spot."""
    await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-blind-1", "name": "Blind Zone"},
        headers=auth_headers,
    )

    resp = await client.get("/watch/alerts/blind-spots", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    names = [bs["name"] for bs in data["blind_spots"]]
    assert "Blind Zone" in names


@pytest.mark.asyncio
async def test_scanned_zone_not_blind(client, auth_headers):
    """Recently scanned zone is not a blind spot."""
    zone_resp = await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-scanned-1", "name": "Scanned Zone"},
        headers=auth_headers,
    )
    zone_id = zone_resp.json()["id"]

    await client.post(
        "/watch/scans",
        json={"zone_id": zone_id, "result_type": "CLEAR"},
        headers=auth_headers,
    )

    resp = await client.get("/watch/alerts/blind-spots", headers=auth_headers)
    data = resp.json()
    blind_names = [bs["name"] for bs in data["blind_spots"]]
    assert "Scanned Zone" not in blind_names


@pytest.mark.asyncio
async def test_alert_test_endpoint(client, auth_headers):
    """Test alert endpoint returns dry_run status."""
    resp = await client.post("/watch/alerts/test", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "sent" in data
    assert "dry_run" in data
    assert data["dry_run"] is True  # No webhook configured in test


@pytest.mark.asyncio
async def test_hostile_scan_fires_alert(client, auth_headers):
    """Hostile scan fires without error (dry run)."""
    zone_resp = await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-hostile-alert", "name": "Hostile Zone"},
        headers=auth_headers,
    )
    zone_id = zone_resp.json()["id"]

    # Should not raise even though webhook is not configured
    resp = await client.post(
        "/watch/scans",
        json={"zone_id": zone_id, "result_type": "HOSTILE"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
