"""Intel module — killmail feed, statistics, and LLM briefing."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_member
from app.config import settings
from app.db.models import (
    CURRENT_CYCLE,
    FeralAIEvent,
    Killmail,
    Member,
    OrbitalZone,
    Scan,
)
from app.db.session import get_db

from .briefing import IntelBriefingService
from .schemas import (
    HourlyKills,
    KillmailDetailResponse,
    KillmailResponse,
    KillmailStatsResponse,
    TopSystem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intel", tags=["intel"])


@router.get("/killmails/stats", response_model=KillmailStatsResponse)
async def killmail_stats(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Kill count by hour for last 24h and top systems."""
    now = datetime.now(timezone.utc)
    t_24h = now - timedelta(hours=24)
    t_7d = now - timedelta(days=7)

    # Total 24h
    total_24h = (
        await db.scalar(
            select(func.count())
            .select_from(Killmail)
            .where(Killmail.timestamp >= t_24h)
        )
        or 0
    )

    # Total 7d
    total_7d = (
        await db.scalar(
            select(func.count()).select_from(Killmail).where(Killmail.timestamp >= t_7d)
        )
        or 0
    )

    # Hourly kills (last 24h) — group by hour
    result = await db.execute(
        select(Killmail.timestamp)
        .where(Killmail.timestamp >= t_24h)
        .order_by(Killmail.timestamp)
    )
    kills_24h = result.scalars().all()

    # Bucket by hour
    hourly: dict[str, int] = {}
    for ts in kills_24h:
        hour_key = ts.strftime("%Y-%m-%dT%H:00:00Z") if ts else "unknown"
        hourly[hour_key] = hourly.get(hour_key, 0) + 1

    hourly_kills = [HourlyKills(hour=h, count=c) for h, c in sorted(hourly.items())]

    # Top 20 systems by kill count
    sys_result = await db.execute(
        select(Killmail.solar_system_id, func.count().label("cnt"))
        .where(Killmail.timestamp >= t_24h, Killmail.solar_system_id.is_not(None))
        .group_by(Killmail.solar_system_id)
        .order_by(func.count().desc())
        .limit(20)
    )
    top_systems = [
        TopSystem(solar_system_id=row[0], count=row[1]) for row in sys_result.all()
    ]

    return KillmailStatsResponse(
        hourly_kills=hourly_kills,
        top_systems=top_systems,
        total_24h=total_24h,
        total_7d=total_7d,
    )


@router.get("/killmails/{kill_id}", response_model=KillmailDetailResponse)
async def get_killmail(
    kill_id: int,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get a single killmail by World API kill_id."""
    result = await db.execute(select(Killmail).where(Killmail.kill_id == kill_id))
    km = result.scalar_one_or_none()
    if not km:
        raise HTTPException(status_code=404, detail="Killmail not found")
    return km


@router.get("/killmails", response_model=list[KillmailResponse])
async def list_killmails(
    corp_name: str | None = Query(
        None, description="Filter by victim or killer corp name"
    ),
    system_id: int | None = Query(None, description="Filter by solar system ID"),
    since: datetime | None = Query(None, description="Only kills after this timestamp"),
    limit: int = Query(50, le=200, ge=1),
    offset: int = Query(0, ge=0),
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """List killmails with optional filters, ordered by timestamp desc."""
    query = select(Killmail)

    if corp_name:
        pattern = f"%{corp_name}%"
        query = query.where(
            Killmail.victim_corp_name.ilike(pattern)
            | Killmail.killer_corp_name.ilike(pattern)
        )
    if system_id is not None:
        query = query.where(Killmail.solar_system_id == system_id)
    if since is not None:
        query = query.where(Killmail.timestamp >= since)

    query = query.order_by(Killmail.timestamp.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


# --- LLM Intel Briefing ---


class BriefingRequest(BaseModel):
    zone_id: UUID
    hours_back: int = 4


class BriefingResponse(BaseModel):
    summary: str
    threat_level: str
    recommended_action: str
    generated_at: str


class BriefingZone(BaseModel):
    zone_id: UUID
    zone_name: str
    scan_count: int
    event_count: int


@router.post("/briefing", response_model=BriefingResponse)
async def generate_briefing(
    body: BriefingRequest,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Generate an LLM-powered intel briefing for a zone."""
    zone = await db.get(OrbitalZone, body.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=body.hours_back)

    # Gather recent scans for this zone
    scan_result = await db.execute(
        select(Scan)
        .where(Scan.zone_id == body.zone_id, Scan.scanned_at >= since)
        .order_by(Scan.scanned_at.desc())
    )
    scans = list(scan_result.scalars().all())

    # Gather recent feral AI events (threats)
    threat_result = await db.execute(
        select(FeralAIEvent)
        .where(FeralAIEvent.zone_id == body.zone_id, FeralAIEvent.timestamp >= since)
        .order_by(FeralAIEvent.timestamp.desc())
    )
    threats = list(threat_result.scalars().all())

    # Hostile scans serve as kill indicators in C5 context
    hostile_scans = [s for s in scans if s.result_type == "HOSTILE"]

    service = IntelBriefingService(api_key=settings.anthropic_api_key)
    brief = await service.generate_brief(
        zone_name=zone.name,
        zone_id=str(body.zone_id),
        hours_back=body.hours_back,
        kills=hostile_scans,
        scans=scans,
        threats=threats,
    )
    return BriefingResponse(**brief)


@router.get("/briefing/zones", response_model=list[BriefingZone])
async def list_briefing_zones(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """List zones with enough data to generate a briefing (1+ scan or event in 24h)."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    zone_result = await db.execute(
        select(OrbitalZone).where(OrbitalZone.cycle == CURRENT_CYCLE)
    )
    zones = zone_result.scalars().all()

    briefing_zones: list[BriefingZone] = []
    for zone in zones:
        scan_count = (
            await db.scalar(
                select(func.count())
                .select_from(Scan)
                .where(Scan.zone_id == zone.id, Scan.scanned_at >= since)
            )
            or 0
        )

        event_count = (
            await db.scalar(
                select(func.count())
                .select_from(FeralAIEvent)
                .where(FeralAIEvent.zone_id == zone.id, FeralAIEvent.timestamp >= since)
            )
            or 0
        )

        if scan_count > 0 or event_count > 0:
            briefing_zones.append(
                BriefingZone(
                    zone_id=zone.id,
                    zone_name=zone.name,
                    scan_count=scan_count,
                    event_count=event_count,
                )
            )

    return briefing_zones
