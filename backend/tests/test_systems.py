"""Tests for System Intelligence endpoints — hotspots and zone activity."""

from datetime import datetime, timedelta, timezone

import pytest

from app.db.models import FeralAIEvent, OrbitalZone, Scan


@pytest.mark.asyncio
async def test_hotspots_empty(client, auth_headers):
    """Hotspots endpoint returns empty list when no zones exist."""
    resp = await client.get("/watch/systems/hotspots", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["hotspots"] == []
    assert "generated_at" in data


@pytest.mark.asyncio
async def test_hotspots_with_zones(client, auth_headers, db_session):
    """Hotspots returns zones ranked by scan count."""
    now = datetime.now(timezone.utc)

    # Create two zones
    zone_a = OrbitalZone(
        zone_id="zone-hot-a",
        name="Hot Alpha",
        feral_ai_tier=2,
        last_scanned=now,
    )
    zone_b = OrbitalZone(
        zone_id="zone-hot-b",
        name="Hot Beta",
        feral_ai_tier=1,
        last_scanned=now,
    )
    db_session.add_all([zone_a, zone_b])
    await db_session.commit()
    await db_session.refresh(zone_a)
    await db_session.refresh(zone_b)

    # Add 3 scans to zone_a, 1 scan to zone_b (all within 24h)
    for i in range(3):
        db_session.add(
            Scan(
                zone_id=zone_a.id,
                result_type="CLEAR",
                scanned_at=now - timedelta(hours=i + 1),
            )
        )
    db_session.add(
        Scan(
            zone_id=zone_b.id,
            result_type="ANOMALY",
            scanned_at=now - timedelta(hours=1),
        )
    )
    await db_session.commit()

    resp = await client.get("/watch/systems/hotspots", headers=auth_headers)
    assert resp.status_code == 200
    hotspots = resp.json()["hotspots"]
    assert len(hotspots) == 2
    # zone_a should be first (more scans)
    assert hotspots[0]["zone_id"] == "zone-hot-a"
    assert hotspots[0]["scan_count_24h"] == 3
    assert hotspots[1]["zone_id"] == "zone-hot-b"
    assert hotspots[1]["scan_count_24h"] == 1


@pytest.mark.asyncio
async def test_hotspots_trend_calculation(client, auth_headers, db_session):
    """Trend is UP when recent 12h has more scans than prior 12h."""
    now = datetime.now(timezone.utc)

    zone = OrbitalZone(
        zone_id="zone-trend",
        name="Trend Zone",
        feral_ai_tier=0,
        last_scanned=now,
    )
    db_session.add(zone)
    await db_session.commit()
    await db_session.refresh(zone)

    # 3 scans in last 12h, 1 scan in prior 12h → trend UP
    for i in range(3):
        db_session.add(
            Scan(
                zone_id=zone.id,
                result_type="CLEAR",
                scanned_at=now - timedelta(hours=i + 1),
            )
        )
    db_session.add(
        Scan(
            zone_id=zone.id,
            result_type="CLEAR",
            scanned_at=now - timedelta(hours=18),
        )
    )
    await db_session.commit()

    resp = await client.get("/watch/systems/hotspots", headers=auth_headers)
    assert resp.status_code == 200
    hotspots = resp.json()["hotspots"]
    assert len(hotspots) == 1
    assert hotspots[0]["trend"] == "UP"
    assert hotspots[0]["scan_count_24h"] == 4


@pytest.mark.asyncio
async def test_system_activity_empty_zone(client, auth_headers, db_session):
    """Activity endpoint returns empty lists for a zone with no scans."""
    zone = OrbitalZone(
        zone_id="zone-empty-act",
        name="Empty Activity",
        feral_ai_tier=0,
    )
    db_session.add(zone)
    await db_session.commit()

    resp = await client.get(
        "/watch/systems/zone-empty-act/activity", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone_id"] == "zone-empty-act"
    assert data["name"] == "Empty Activity"
    assert len(data["hourly_scans"]) == 24
    assert all(h["count"] == 0 for h in data["hourly_scans"])
    assert data["threat_history"] == []
    assert data["recent_scans"] == []
    assert data["active_scanners"] == []


@pytest.mark.asyncio
async def test_system_activity_with_scans(client, auth_headers, db_session):
    """Activity returns scans, scanners, and threat history."""
    now = datetime.now(timezone.utc)

    zone = OrbitalZone(
        zone_id="zone-act-full",
        name="Full Activity",
        feral_ai_tier=3,
        last_scanned=now,
    )
    db_session.add(zone)
    await db_session.commit()
    await db_session.refresh(zone)

    # Add scans
    for i in range(5):
        db_session.add(
            Scan(
                zone_id=zone.id,
                result_type="HOSTILE" if i == 0 else "CLEAR",
                signature_type="EM",
                resolution=50 + i * 10,
                scanned_at=now - timedelta(hours=i),
            )
        )

    # Add feral AI event
    db_session.add(
        FeralAIEvent(
            zone_id=zone.id,
            event_type="evolved",
            severity=3,
            previous_tier=2,
            new_tier=3,
            timestamp=now - timedelta(hours=2),
        )
    )
    await db_session.commit()

    resp = await client.get(
        "/watch/systems/zone-act-full/activity", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone_id"] == "zone-act-full"
    assert data["name"] == "Full Activity"
    assert len(data["recent_scans"]) == 5
    assert data["recent_scans"][0]["result_type"] == "HOSTILE"
    assert len(data["threat_history"]) == 1
    assert data["threat_history"][0]["tier"] == 3


@pytest.mark.asyncio
async def test_system_activity_zone_not_found(client, auth_headers):
    """Activity endpoint returns 404 for unknown zone."""
    resp = await client.get(
        "/watch/systems/nonexistent-zone/activity", headers=auth_headers
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Zone not found"
