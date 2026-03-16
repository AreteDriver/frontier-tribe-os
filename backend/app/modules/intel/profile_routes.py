"""Pilot and corp intelligence profile endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_member
from app.db.models import Killmail, Member
from app.db.session import get_db

from .schemas import (
    ActiveHour,
    CorpLeaderboardEntry,
    CorpProfileResponse,
    KillmailResponse,
    PilotProfileResponse,
    PilotSearchResult,
    TopKiller,
    TopSystem,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _threat_level(kill_count: int) -> str:
    if kill_count >= 30:
        return "CRITICAL"
    if kill_count >= 15:
        return "HIGH"
    if kill_count >= 5:
        return "MEDIUM"
    return "LOW"


@router.get("/pilots/search", response_model=list[PilotSearchResult])
async def search_pilots(
    q: str = Query(..., min_length=1, description="Search by pilot name"),
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Search pilots by name across killmail data."""
    pattern = f"%{q}%"

    killer_q = select(
        Killmail.killer_address.label("address"),
        Killmail.killer_name.label("name"),
    ).where(Killmail.killer_name.ilike(pattern))

    victim_q = select(
        Killmail.victim_address.label("address"),
        Killmail.victim_name.label("name"),
    ).where(Killmail.victim_name.ilike(pattern))

    union_q = killer_q.union(victim_q).limit(20)
    result = await db.execute(union_q)
    rows = result.all()

    seen: dict[str, PilotSearchResult] = {}
    for row in rows:
        addr = row[0]
        if addr not in seen:
            seen[addr] = PilotSearchResult(address=addr, name=row[1])

    return list(seen.values())


@router.get("/pilots/{address}", response_model=PilotProfileResponse)
async def pilot_profile(
    address: str,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get pilot intelligence profile from killmail data."""
    kill_count = (
        await db.scalar(
            select(func.count())
            .select_from(Killmail)
            .where(Killmail.killer_address == address)
        )
        or 0
    )

    death_count = (
        await db.scalar(
            select(func.count())
            .select_from(Killmail)
            .where(Killmail.victim_address == address)
        )
        or 0
    )

    if kill_count == 0 and death_count == 0:
        raise HTTPException(status_code=404, detail="Pilot not found in killmail data")

    kd_ratio = (
        round(kill_count / death_count, 2) if death_count > 0 else float(kill_count)
    )

    latest_km = await db.execute(
        select(Killmail)
        .where(
            (Killmail.killer_address == address) | (Killmail.victim_address == address)
        )
        .order_by(Killmail.timestamp.desc())
        .limit(1)
    )
    latest = latest_km.scalar_one_or_none()
    name = None
    if latest:
        if latest.killer_address == address:
            name = latest.killer_name
        else:
            name = latest.victim_name

    sys_result = await db.execute(
        select(Killmail.solar_system_id, func.count().label("cnt"))
        .where(
            (Killmail.killer_address == address) | (Killmail.victim_address == address),
            Killmail.solar_system_id.is_not(None),
        )
        .group_by(Killmail.solar_system_id)
        .order_by(func.count().desc())
        .limit(3)
    )
    primary_systems = [
        TopSystem(solar_system_id=row[0], count=row[1]) for row in sys_result.all()
    ]

    all_timestamps = await db.execute(
        select(Killmail.timestamp).where(
            (Killmail.killer_address == address) | (Killmail.victim_address == address)
        )
    )
    hour_counts: dict[int, int] = {}
    for (ts,) in all_timestamps.all():
        if ts:
            h = ts.hour
            hour_counts[h] = hour_counts.get(h, 0) + 1
    active_hours = [ActiveHour(hour=h, count=c) for h, c in sorted(hour_counts.items())]

    recent_result = await db.execute(
        select(Killmail)
        .where(
            (Killmail.killer_address == address) | (Killmail.victim_address == address)
        )
        .order_by(Killmail.timestamp.desc())
        .limit(10)
    )
    recent_kills = [
        KillmailResponse.model_validate(km, from_attributes=True)
        for km in recent_result.scalars().all()
    ]

    first_seen_ts = await db.scalar(
        select(func.min(Killmail.timestamp)).where(
            (Killmail.killer_address == address) | (Killmail.victim_address == address)
        )
    )
    last_seen_ts = await db.scalar(
        select(func.max(Killmail.timestamp)).where(
            (Killmail.killer_address == address) | (Killmail.victim_address == address)
        )
    )

    return PilotProfileResponse(
        address=address,
        name=name,
        kill_count=kill_count,
        death_count=death_count,
        kd_ratio=kd_ratio,
        primary_systems=primary_systems,
        active_hours=active_hours,
        recent_kills=recent_kills,
        first_seen=first_seen_ts,
        last_seen=last_seen_ts,
        threat_level=_threat_level(kill_count),
    )


@router.get("/corps/leaderboard", response_model=list[CorpLeaderboardEntry])
async def corp_leaderboard(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Top 10 corps by kill count."""
    result = await db.execute(
        select(
            Killmail.killer_corp_id,
            Killmail.killer_corp_name,
            func.count().label("cnt"),
        )
        .where(Killmail.killer_corp_id.is_not(None))
        .group_by(Killmail.killer_corp_id, Killmail.killer_corp_name)
        .order_by(func.count().desc())
        .limit(10)
    )
    return [
        CorpLeaderboardEntry(corp_id=row[0], corp_name=row[1], kill_count=row[2])
        for row in result.all()
    ]


@router.get("/corps/{corp_id}", response_model=CorpProfileResponse)
async def corp_profile(
    corp_id: int,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get corp intelligence profile from killmail data."""
    kill_count = (
        await db.scalar(
            select(func.count())
            .select_from(Killmail)
            .where(Killmail.killer_corp_id == corp_id)
        )
        or 0
    )

    death_count = (
        await db.scalar(
            select(func.count())
            .select_from(Killmail)
            .where(Killmail.victim_corp_id == corp_id)
        )
        or 0
    )

    if kill_count == 0 and death_count == 0:
        raise HTTPException(status_code=404, detail="Corp not found in killmail data")

    total = kill_count + death_count
    efficiency = round((kill_count / total) * 100, 1) if total > 0 else 0.0

    latest = await db.execute(
        select(Killmail)
        .where(
            (Killmail.killer_corp_id == corp_id) | (Killmail.victim_corp_id == corp_id)
        )
        .order_by(Killmail.timestamp.desc())
        .limit(1)
    )
    latest_km = latest.scalar_one_or_none()
    corp_name = None
    if latest_km:
        if latest_km.killer_corp_id == corp_id:
            corp_name = latest_km.killer_corp_name
        else:
            corp_name = latest_km.victim_corp_name

    killer_addrs = await db.execute(
        select(Killmail.killer_address)
        .where(Killmail.killer_corp_id == corp_id)
        .distinct()
    )
    victim_addrs = await db.execute(
        select(Killmail.victim_address)
        .where(Killmail.victim_corp_id == corp_id)
        .distinct()
    )
    member_set: set[str] = set()
    for (addr,) in killer_addrs.all():
        member_set.add(addr)
    for (addr,) in victim_addrs.all():
        member_set.add(addr)

    sys_result = await db.execute(
        select(Killmail.solar_system_id, func.count().label("cnt"))
        .where(
            (Killmail.killer_corp_id == corp_id) | (Killmail.victim_corp_id == corp_id),
            Killmail.solar_system_id.is_not(None),
        )
        .group_by(Killmail.solar_system_id)
        .order_by(func.count().desc())
        .limit(3)
    )
    primary_systems = [
        TopSystem(solar_system_id=row[0], count=row[1]) for row in sys_result.all()
    ]

    recent_result = await db.execute(
        select(Killmail)
        .where(
            (Killmail.killer_corp_id == corp_id) | (Killmail.victim_corp_id == corp_id)
        )
        .order_by(Killmail.timestamp.desc())
        .limit(10)
    )
    recent_kills = [
        KillmailResponse.model_validate(km, from_attributes=True)
        for km in recent_result.scalars().all()
    ]

    top_result = await db.execute(
        select(
            Killmail.killer_address,
            Killmail.killer_name,
            func.count().label("cnt"),
        )
        .where(Killmail.killer_corp_id == corp_id)
        .group_by(Killmail.killer_address, Killmail.killer_name)
        .order_by(func.count().desc())
        .limit(5)
    )
    top_killers = [
        TopKiller(address=row[0], name=row[1], kill_count=row[2])
        for row in top_result.all()
    ]

    return CorpProfileResponse(
        corp_id=corp_id,
        corp_name=corp_name,
        kill_count=kill_count,
        death_count=death_count,
        efficiency=efficiency,
        member_addresses=sorted(member_set),
        primary_systems=primary_systems,
        recent_kills=recent_kills,
        top_killers=top_killers,
    )
