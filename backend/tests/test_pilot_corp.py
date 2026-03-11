"""Tests for Pilot Intelligence, Corp Intelligence, and Global Search endpoints."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Killmail, OrbitalZone


async def _seed_killmail(
    db: AsyncSession,
    kill_id: int,
    killer_address: str = "0xkiller1",
    killer_name: str = "AlphaWolf",
    killer_corp_id: int | None = 100,
    killer_corp_name: str | None = "Wolves of War",
    victim_address: str = "0xvictim1",
    victim_name: str = "PoorSoul",
    victim_corp_id: int | None = 200,
    victim_corp_name: str | None = "Peaceful Corp",
    solar_system_id: int | None = 30001000,
    timestamp: datetime | None = None,
) -> Killmail:
    if timestamp is None:
        timestamp = datetime.now(timezone.utc) - timedelta(hours=1)
    km = Killmail(
        id=uuid.uuid4(),
        kill_id=kill_id,
        killer_address=killer_address,
        killer_name=killer_name,
        killer_corp_id=killer_corp_id,
        killer_corp_name=killer_corp_name,
        victim_address=victim_address,
        victim_name=victim_name,
        victim_corp_id=victim_corp_id,
        victim_corp_name=victim_corp_name,
        solar_system_id=solar_system_id,
        timestamp=timestamp,
    )
    db.add(km)
    await db.commit()
    return km


# --- Pilot Profile ---


@pytest.mark.asyncio
async def test_pilot_profile_not_found(client, auth_headers):
    """Address with no kills returns 404."""
    resp = await client.get("/intel/pilots/0xnonexistent", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pilot_profile_with_kills(client, auth_headers, db_session):
    """Seed killmails, verify pilot stats are computed correctly."""
    now = datetime.now(timezone.utc)
    # 3 kills as killer
    for i in range(3):
        await _seed_killmail(
            db_session,
            kill_id=1000 + i,
            killer_address="0xace",
            killer_name="AcePilot",
            victim_address=f"0xvictim{i}",
            solar_system_id=30001000 if i < 2 else 30002000,
            timestamp=now - timedelta(hours=i),
        )
    # 1 death as victim
    await _seed_killmail(
        db_session,
        kill_id=1010,
        killer_address="0xsomeone",
        victim_address="0xace",
        victim_name="AcePilot",
        solar_system_id=30001000,
        timestamp=now - timedelta(hours=5),
    )

    resp = await client.get("/intel/pilots/0xace", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["address"] == "0xace"
    assert data["name"] == "AcePilot"
    assert data["kill_count"] == 3
    assert data["death_count"] == 1
    assert data["kd_ratio"] == 3.0
    assert data["threat_level"] == "LOW"  # 3 kills = LOW
    assert len(data["primary_systems"]) >= 1
    assert data["primary_systems"][0]["solar_system_id"] == 30001000
    assert len(data["recent_kills"]) == 4
    assert data["first_seen"] is not None
    assert data["last_seen"] is not None


# --- Pilot Search ---


@pytest.mark.asyncio
async def test_pilot_search(client, auth_headers, db_session):
    """Search by pilot name finds matching pilots."""
    await _seed_killmail(
        db_session,
        kill_id=2000,
        killer_address="0xsearcher",
        killer_name="ShadowBlade",
    )
    await _seed_killmail(
        db_session,
        kill_id=2001,
        victim_address="0xvictimsearch",
        victim_name="ShadowFox",
    )

    resp = await client.get(
        "/intel/pilots/search", params={"q": "Shadow"}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    addresses = {p["address"] for p in data}
    assert "0xsearcher" in addresses
    assert "0xvictimsearch" in addresses


# --- Corp Profile ---


@pytest.mark.asyncio
async def test_corp_profile_not_found(client, auth_headers):
    """Corp with no kills returns 404."""
    resp = await client.get("/intel/corps/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_corp_profile_with_kills(client, auth_headers, db_session):
    """Seed killmails, verify corp stats."""
    now = datetime.now(timezone.utc)
    # 2 kills by corp 500
    for i in range(2):
        await _seed_killmail(
            db_session,
            kill_id=3000 + i,
            killer_address=f"0xcorpmember{i}",
            killer_name=f"Member{i}",
            killer_corp_id=500,
            killer_corp_name="Elite Corp",
            victim_corp_id=600,
            solar_system_id=30003000,
            timestamp=now - timedelta(hours=i),
        )
    # 1 death for corp 500
    await _seed_killmail(
        db_session,
        kill_id=3010,
        killer_corp_id=600,
        victim_address="0xcorpmember0",
        victim_name="Member0",
        victim_corp_id=500,
        victim_corp_name="Elite Corp",
        solar_system_id=30003000,
        timestamp=now - timedelta(hours=3),
    )

    resp = await client.get("/intel/corps/500", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["corp_id"] == 500
    assert data["corp_name"] == "Elite Corp"
    assert data["kill_count"] == 2
    assert data["death_count"] == 1
    assert data["efficiency"] == pytest.approx(66.7, abs=0.1)
    assert len(data["member_addresses"]) >= 2  # 2 killer + 1 victim address
    assert len(data["top_killers"]) >= 1
    assert len(data["recent_kills"]) == 3


# --- Corp Leaderboard ---


@pytest.mark.asyncio
async def test_corp_leaderboard_empty(client, auth_headers):
    """Empty DB returns empty leaderboard."""
    resp = await client.get("/intel/corps/leaderboard", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_corp_leaderboard_with_data(client, auth_headers, db_session):
    """Leaderboard shows top corps by kill count."""
    now = datetime.now(timezone.utc)
    # Corp 700: 3 kills
    for i in range(3):
        await _seed_killmail(
            db_session,
            kill_id=4000 + i,
            killer_corp_id=700,
            killer_corp_name="Top Corp",
            timestamp=now - timedelta(hours=i),
        )
    # Corp 800: 1 kill
    await _seed_killmail(
        db_session,
        kill_id=4010,
        killer_corp_id=800,
        killer_corp_name="Second Corp",
        timestamp=now - timedelta(hours=1),
    )

    resp = await client.get("/intel/corps/leaderboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["corp_id"] == 700
    assert data[0]["kill_count"] == 3
    assert data[1]["corp_id"] == 800
    assert data[1]["kill_count"] == 1


# --- Global Search ---


@pytest.mark.asyncio
async def test_global_search_empty(client, auth_headers):
    """Query too short returns 422 (min_length=2 validation)."""
    resp = await client.get("/intel/search", params={"q": "x"}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_global_search_pilots(client, auth_headers, db_session):
    """Search finds pilots by name."""
    await _seed_killmail(
        db_session,
        kill_id=5000,
        killer_address="0xsearchpilot1",
        killer_name="NovaBlade",
    )
    await _seed_killmail(
        db_session,
        kill_id=5001,
        victim_address="0xsearchpilot2",
        victim_name="NovaStrike",
    )

    resp = await client.get("/intel/search", params={"q": "Nova"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    addresses = {p["address"] for p in data["pilots"]}
    assert "0xsearchpilot1" in addresses
    assert "0xsearchpilot2" in addresses
    assert len(data["pilots"]) <= 5


@pytest.mark.asyncio
async def test_global_search_zones(client, auth_headers, db_session):
    """Search finds zones by name."""
    zone = OrbitalZone(
        id=uuid.uuid4(),
        zone_id="zone-alpha-1",
        name="Alpha Nexus",
        feral_ai_tier=0,
        cycle=5,
    )
    db_session.add(zone)
    await db_session.commit()

    resp = await client.get(
        "/intel/search", params={"q": "Alpha"}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    zone_names = {z["name"] for z in data["zones"]}
    assert "Alpha Nexus" in zone_names
    assert data["zones"][0]["zone_id"] == "zone-alpha-1"
