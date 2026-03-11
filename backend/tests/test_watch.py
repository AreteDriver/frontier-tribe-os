"""Tests for the Watch module — C5 cycle, orbital zones, scans, clones, crowns."""

import pytest


@pytest.mark.asyncio
async def test_cycle_endpoint(client, auth_headers):
    """Cycle endpoint returns current cycle info."""
    resp = await client.get("/watch/cycle", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["cycle"] == 5
    assert data["cycle_name"] == "Shroud of Fear"
    assert "reset_at" in data
    assert "days_elapsed" in data


@pytest.mark.asyncio
async def test_create_orbital_zone(client, auth_headers):
    """Can create an orbital zone."""
    resp = await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-alpha-1", "name": "Alpha Sector"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["zone_id"] == "zone-alpha-1"
    assert data["name"] == "Alpha Sector"
    assert data["threat_level"] == "DORMANT"
    assert data["feral_ai_tier"] == 0
    assert data["scan_stale"] is True


@pytest.mark.asyncio
async def test_create_duplicate_zone(client, auth_headers):
    """Duplicate zone_id returns 409."""
    await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-dup", "name": "Dup Zone"},
        headers=auth_headers,
    )
    resp = await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-dup", "name": "Dup Zone 2"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_orbital_zones(client, auth_headers):
    """List zones returns created zones."""
    await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-list-1", "name": "Zone One"},
        headers=auth_headers,
    )
    await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-list-2", "name": "Zone Two", "feral_ai_tier": 3},
        headers=auth_headers,
    )
    resp = await client.get("/watch/orbital-zones", headers=auth_headers)
    assert resp.status_code == 200
    zones = resp.json()
    assert len(zones) >= 2


@pytest.mark.asyncio
async def test_filter_zones_by_threat(client, auth_headers):
    """Filter zones by threat level."""
    await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-crit", "name": "Critical Zone", "feral_ai_tier": 3},
        headers=auth_headers,
    )
    await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-dorm", "name": "Dormant Zone", "feral_ai_tier": 0},
        headers=auth_headers,
    )
    resp = await client.get(
        "/watch/orbital-zones?threat_level=CRITICAL", headers=auth_headers
    )
    assert resp.status_code == 200
    for z in resp.json():
        assert z["threat_level"] == "CRITICAL"


@pytest.mark.asyncio
async def test_submit_scan(client, auth_headers):
    """Submit a scan result for a zone."""
    zone_resp = await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-scan-1", "name": "Scan Zone"},
        headers=auth_headers,
    )
    zone_id = zone_resp.json()["id"]

    resp = await client.post(
        "/watch/scans",
        json={"zone_id": zone_id, "result_type": "CLEAR", "confidence": 95},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["result_type"] == "CLEAR"
    assert data["confidence"] == 95


@pytest.mark.asyncio
async def test_submit_scan_invalid_type(client, auth_headers):
    """Invalid scan result_type returns 400."""
    zone_resp = await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-scan-bad", "name": "Bad Scan Zone"},
        headers=auth_headers,
    )
    zone_id = zone_resp.json()["id"]

    resp = await client.post(
        "/watch/scans",
        json={"zone_id": zone_id, "result_type": "INVALID"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_scan_feed(client, auth_headers):
    """Scan feed returns recent scans."""
    zone_resp = await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-feed-1", "name": "Feed Zone"},
        headers=auth_headers,
    )
    zone_id = zone_resp.json()["id"]

    await client.post(
        "/watch/scans",
        json={"zone_id": zone_id, "result_type": "HOSTILE"},
        headers=auth_headers,
    )

    resp = await client.get("/watch/scans/feed", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_scan_updates_last_scanned(client, auth_headers):
    """Submitting a scan updates the zone's last_scanned."""
    zone_resp = await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-scan-update", "name": "Update Zone"},
        headers=auth_headers,
    )
    zone_id = zone_resp.json()["id"]
    assert zone_resp.json()["last_scanned"] is None

    await client.post(
        "/watch/scans",
        json={"zone_id": zone_id, "result_type": "CLEAR"},
        headers=auth_headers,
    )

    # Fetch zones and check last_scanned is set
    zones_resp = await client.get("/watch/orbital-zones", headers=auth_headers)
    updated = [z for z in zones_resp.json() if z["zone_id"] == "zone-scan-update"]
    assert len(updated) == 1
    assert updated[0]["last_scanned"] is not None


@pytest.mark.asyncio
async def test_zone_history_empty(client, auth_headers):
    """Zone history returns empty for new zone."""
    zone_resp = await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-hist", "name": "History Zone"},
        headers=auth_headers,
    )
    zone_id = zone_resp.json()["id"]

    resp = await client.get(
        f"/watch/orbital-zones/{zone_id}/history", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_clones_no_tribe(client, auth_headers):
    """Clones endpoint returns 400 if member has no tribe."""
    # Note: auth_headers member doesn't have a tribe by default
    # Need to create tribe first for positive test
    resp = await client.get("/watch/clones", headers=auth_headers)
    # Dev-login member starts without tribe
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_clones_with_tribe(client, tribe_with_leader):
    """Clones endpoint returns empty queue for new tribe."""
    tribe, headers = tribe_with_leader
    resp = await client.get("/watch/clones", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_active"] == 0
    assert data["total_manufacturing"] == 0
    assert data["low_reserve"] is True


@pytest.mark.asyncio
async def test_crown_roster_with_tribe(client, tribe_with_leader):
    """Crown roster returns empty for new tribe."""
    tribe, headers = tribe_with_leader
    resp = await client.get("/watch/crowns/roster", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_members"] == 1
    assert data["members_with_crowns"] == 0
    assert data["crown_type_distribution"] == {}
