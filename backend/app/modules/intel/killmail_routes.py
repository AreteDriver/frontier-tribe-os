"""Killmail feed and statistics endpoints."""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_member
from app.db.models import Killmail, Member
from app.db.session import get_db

from .schemas import (
    HourlyKills,
    KillmailDetailResponse,
    KillmailResponse,
    KillmailStatsResponse,
    TopSystem,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/killmails/stats", response_model=KillmailStatsResponse)
async def killmail_stats(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Kill count by hour for last 24h and top systems."""
    now = datetime.now(timezone.utc)
    t_24h = now - timedelta(hours=24)
    t_7d = now - timedelta(days=7)

    total_24h = (
        await db.scalar(
            select(func.count())
            .select_from(Killmail)
            .where(Killmail.timestamp >= t_24h)
        )
        or 0
    )

    total_7d = (
        await db.scalar(
            select(func.count()).select_from(Killmail).where(Killmail.timestamp >= t_7d)
        )
        or 0
    )

    result = await db.execute(
        select(Killmail.timestamp)
        .where(Killmail.timestamp >= t_24h)
        .order_by(Killmail.timestamp)
    )
    kills_24h = result.scalars().all()

    hourly: dict[str, int] = {}
    for ts in kills_24h:
        hour_key = ts.strftime("%Y-%m-%dT%H:00:00Z") if ts else "unknown"
        hourly[hour_key] = hourly.get(hour_key, 0) + 1

    hourly_kills = [HourlyKills(hour=h, count=c) for h, c in sorted(hourly.items())]

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
