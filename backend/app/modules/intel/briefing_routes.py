"""LLM intel briefing endpoints."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_member
from app.config import settings
from app.db.models import CURRENT_CYCLE, FeralAIEvent, Member, OrbitalZone, Scan
from app.db.session import get_db

from .briefing import IntelBriefingService

logger = logging.getLogger(__name__)

router = APIRouter()


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

    scan_result = await db.execute(
        select(Scan)
        .where(Scan.zone_id == body.zone_id, Scan.scanned_at >= since)
        .order_by(Scan.scanned_at.desc())
    )
    scans = list(scan_result.scalars().all())

    threat_result = await db.execute(
        select(FeralAIEvent)
        .where(FeralAIEvent.zone_id == body.zone_id, FeralAIEvent.timestamp >= since)
        .order_by(FeralAIEvent.timestamp.desc())
    )
    threats = list(threat_result.scalars().all())

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
