"""Tests for the Intel module — killmail feed and statistics."""

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Killmail


async def _create_killmail(
    db: AsyncSession,
    kill_id: int,
    victim_name: str = "VictimPilot",
    killer_name: str = "KillerPilot",
    victim_corp_name: str | None = None,
    killer_corp_name: str | None = None,
    solar_system_id: int | None = 30023604,
    timestamp: datetime | None = None,
) -> Killmail:
    """Helper to insert a killmail into the test DB."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc) - timedelta(hours=1)
    km = Killmail(
        id=uuid.uuid4(),
        kill_id=kill_id,
        victim_address="0xvictim",
        victim_name=victim_name,
        victim_corp_name=victim_corp_name,
        killer_address="0xkiller",
        killer_name=killer_name,
        killer_corp_name=killer_corp_name,
        solar_system_id=solar_system_id,
        timestamp=timestamp,
        raw_json=json.dumps({"id": kill_id}),
    )
    db.add(km)
    await db.commit()
    return km


@pytest.mark.asyncio
async def test_list_killmails_empty(client, auth_headers):
    """Empty DB returns empty list."""
    resp = await client.get("/intel/killmails", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_killmails_with_data(client, auth_headers, db_session):
    """Killmails in DB appear in response."""
    await _create_killmail(db_session, kill_id=100, victim_name="TestVictim")

    resp = await client.get("/intel/killmails", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["kill_id"] == 100
    assert data[0]["victim_name"] == "TestVictim"
    assert "time_ago" in data[0]


@pytest.mark.asyncio
async def test_list_killmails_filter_by_corp(client, auth_headers, db_session):
    """Filter by corp_name matches victim or killer corp."""
    await _create_killmail(db_session, kill_id=200, victim_corp_name="Wolves of War")
    await _create_killmail(db_session, kill_id=201, killer_corp_name="Shadow Syndicate")
    await _create_killmail(db_session, kill_id=202, victim_corp_name="Neutral Corp")

    resp = await client.get(
        "/intel/killmails", params={"corp_name": "Wolves"}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["kill_id"] == 200


@pytest.mark.asyncio
async def test_list_killmails_pagination(client, auth_headers, db_session):
    """Limit and offset work correctly."""
    for i in range(5):
        await _create_killmail(
            db_session,
            kill_id=300 + i,
            timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
        )

    resp = await client.get(
        "/intel/killmails", params={"limit": 2, "offset": 0}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # Most recent first
    assert data[0]["kill_id"] == 300

    # Second page
    resp2 = await client.get(
        "/intel/killmails", params={"limit": 2, "offset": 2}, headers=auth_headers
    )
    data2 = resp2.json()
    assert len(data2) == 2
    assert data2[0]["kill_id"] == 302


@pytest.mark.asyncio
async def test_get_single_killmail(client, auth_headers, db_session):
    """Single killmail by kill_id returns detail with raw_json."""
    await _create_killmail(db_session, kill_id=400, victim_name="DetailVictim")

    resp = await client.get("/intel/killmails/400", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["kill_id"] == 400
    assert data["victim_name"] == "DetailVictim"
    assert "raw_json" in data


@pytest.mark.asyncio
async def test_get_killmail_not_found(client, auth_headers):
    """Non-existent kill_id returns 404."""
    resp = await client.get("/intel/killmails/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_killmail_stats_empty(client, auth_headers):
    """Stats with no data returns zeros."""
    resp = await client.get("/intel/killmails/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_24h"] == 0
    assert data["total_7d"] == 0
    assert data["hourly_kills"] == []
    assert data["top_systems"] == []


@pytest.mark.asyncio
async def test_killmail_stats_with_data(client, auth_headers, db_session):
    """Stats reflect inserted killmails."""
    now = datetime.now(timezone.utc)
    # 3 kills in the last hour, 1 kill 2 days ago
    for i in range(3):
        await _create_killmail(
            db_session,
            kill_id=500 + i,
            solar_system_id=30001000,
            timestamp=now - timedelta(minutes=10 + i),
        )
    await _create_killmail(
        db_session,
        kill_id=503,
        solar_system_id=30002000,
        timestamp=now - timedelta(days=2),
    )

    resp = await client.get("/intel/killmails/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_24h"] == 3
    assert data["total_7d"] == 4
    assert len(data["top_systems"]) >= 1
    # System 30001000 should be top
    assert data["top_systems"][0]["solar_system_id"] == 30001000
    assert data["top_systems"][0]["count"] == 3
