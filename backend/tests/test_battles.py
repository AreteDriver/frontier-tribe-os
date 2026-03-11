"""Tests for the Battle Report feature — multi-side kill reconstruction."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Killmail


async def _seed_killmail(
    db: AsyncSession,
    kill_id: int,
    solar_system_id: int = 30001000,
    killer_address: str = "0xkiller1",
    killer_name: str = "Killer1",
    killer_corp_id: int | None = 100,
    killer_corp_name: str | None = "Wolves",
    victim_address: str = "0xvictim1",
    victim_name: str = "Victim1",
    victim_corp_id: int | None = 200,
    victim_corp_name: str | None = "Bears",
    timestamp: datetime | None = None,
) -> Killmail:
    """Insert a killmail for battle tests."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc) - timedelta(hours=1)
    km = Killmail(
        id=uuid.uuid4(),
        kill_id=kill_id,
        solar_system_id=solar_system_id,
        killer_address=killer_address,
        killer_name=killer_name,
        killer_corp_id=killer_corp_id,
        killer_corp_name=killer_corp_name,
        victim_address=victim_address,
        victim_name=victim_name,
        victim_corp_id=victim_corp_id,
        victim_corp_name=victim_corp_name,
        timestamp=timestamp,
    )
    db.add(km)
    await db.commit()
    return km


@pytest.mark.asyncio
async def test_battles_empty(client, auth_headers):
    """No killmails yields empty battle list."""
    resp = await client.get("/intel/battles", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_battles_single_kill_no_battle(client, auth_headers, db_session):
    """A single kill does not qualify as a battle (needs 3+)."""
    await _seed_killmail(db_session, kill_id=1000)
    resp = await client.get("/intel/battles", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_battles_two_kills_no_battle(client, auth_headers, db_session):
    """Two kills in same system still below threshold."""
    base = datetime.now(timezone.utc) - timedelta(hours=1)
    await _seed_killmail(db_session, kill_id=1100, timestamp=base)
    await _seed_killmail(
        db_session, kill_id=1101, timestamp=base + timedelta(minutes=5)
    )
    resp = await client.get("/intel/battles", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_battles_cluster_detected(client, auth_headers, db_session):
    """4 kills in same system within 30 min window form a battle."""
    base = datetime.now(timezone.utc) - timedelta(hours=2)
    for i in range(4):
        await _seed_killmail(
            db_session,
            kill_id=2000 + i,
            solar_system_id=30005000,
            killer_address=f"0xkiller{i}",
            killer_name=f"Killer{i}",
            killer_corp_id=100,
            killer_corp_name="Wolves",
            victim_address=f"0xvictim{i}",
            victim_name=f"Victim{i}",
            victim_corp_id=200,
            victim_corp_name="Bears",
            timestamp=base + timedelta(minutes=i * 5),
        )

    resp = await client.get("/intel/battles", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1

    battle = data[0]
    assert battle["solar_system_id"] == 30005000
    assert battle["total_kills"] == 4
    assert len(battle["sides"]) >= 2
    assert len(battle["preview"]) <= 3
    assert battle["battle_id"]  # non-empty hash


@pytest.mark.asyncio
async def test_battle_detail(client, auth_headers, db_session):
    """Battle detail returns sides, timeline, and duration."""
    base = datetime.now(timezone.utc) - timedelta(hours=2)
    for i in range(4):
        await _seed_killmail(
            db_session,
            kill_id=3000 + i,
            solar_system_id=30006000,
            killer_address=f"0xkiller{i}",
            killer_name=f"Attacker{i}",
            killer_corp_id=100,
            killer_corp_name="Wolves",
            victim_address=f"0xvictim{i}",
            victim_name=f"Defender{i}",
            victim_corp_id=200,
            victim_corp_name="Bears",
            timestamp=base + timedelta(minutes=i * 7),
        )

    # First get the battle list to find the battle_id
    list_resp = await client.get("/intel/battles", headers=auth_headers)
    assert list_resp.status_code == 200
    battles = list_resp.json()
    assert len(battles) == 1
    battle_id = battles[0]["battle_id"]

    # Get detail
    detail_resp = await client.get(f"/intel/battles/{battle_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()

    assert detail["battle_id"] == battle_id
    assert detail["solar_system_id"] == 30006000
    assert detail["total_kills"] == 4
    assert detail["duration_minutes"] >= 0
    assert len(detail["timeline"]) == 4
    assert len(detail["sides"]) >= 2

    # Verify timeline is ordered by timestamp
    timestamps = [e["timestamp"] for e in detail["timeline"]]
    assert timestamps == sorted(timestamps)

    # Verify sides have correct stats
    wolves = next((s for s in detail["sides"] if s["corp_name"] == "Wolves"), None)
    bears = next((s for s in detail["sides"] if s["corp_name"] == "Bears"), None)
    assert wolves is not None
    assert bears is not None
    assert wolves["kill_count"] == 4
    assert wolves["death_count"] == 0
    assert bears["kill_count"] == 0
    assert bears["death_count"] == 4

    # Narrative is None without API key
    assert detail["narrative"] is None


@pytest.mark.asyncio
async def test_battle_not_found(client, auth_headers):
    """Invalid battle_id returns 404."""
    resp = await client.get("/intel/battles/nonexistent", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_battles_separate_systems(client, auth_headers, db_session):
    """Kills in different systems form separate battles."""
    base = datetime.now(timezone.utc) - timedelta(hours=2)
    # 3 kills in system A
    for i in range(3):
        await _seed_killmail(
            db_session,
            kill_id=4000 + i,
            solar_system_id=30007000,
            timestamp=base + timedelta(minutes=i * 5),
        )
    # 3 kills in system B
    for i in range(3):
        await _seed_killmail(
            db_session,
            kill_id=4100 + i,
            solar_system_id=30008000,
            timestamp=base + timedelta(minutes=i * 5),
        )

    resp = await client.get("/intel/battles", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    system_ids = {b["solar_system_id"] for b in data}
    assert system_ids == {30007000, 30008000}


@pytest.mark.asyncio
async def test_battles_time_gap_splits_clusters(client, auth_headers, db_session):
    """Kills > 30 min apart in same system form separate clusters."""
    base = datetime.now(timezone.utc) - timedelta(hours=4)
    # First cluster: 3 kills
    for i in range(3):
        await _seed_killmail(
            db_session,
            kill_id=5000 + i,
            solar_system_id=30009000,
            timestamp=base + timedelta(minutes=i * 5),
        )
    # Second cluster: 3 kills, 2 hours later
    for i in range(3):
        await _seed_killmail(
            db_session,
            kill_id=5100 + i,
            solar_system_id=30009000,
            timestamp=base + timedelta(hours=2, minutes=i * 5),
        )

    resp = await client.get("/intel/battles", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # Both in same system
    assert all(b["solar_system_id"] == 30009000 for b in data)
