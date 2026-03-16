"""Intel module — aggregates sub-routers for killmails, profiles, battles, and briefings."""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_member
from app.db.models import Killmail, Member, OrbitalZone
from app.db.session import get_db

from .battle_routes import router as battle_router
from .briefing_routes import router as briefing_router
from .killmail_routes import router as killmail_router
from .profile_routes import router as profile_router
from .schemas import (
    GlobalSearchResponse,
    SearchCorpResult,
    SearchPilotResult,
    SearchZoneResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intel", tags=["intel"])
router.include_router(killmail_router)
router.include_router(profile_router)
router.include_router(battle_router)
router.include_router(briefing_router)


@router.get("/search", response_model=GlobalSearchResponse)
async def global_search(
    q: str = Query(..., min_length=2, description="Search query (min 2 chars)"),
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Unified search across pilots, corps, and zones."""
    pattern = f"%{q}%"

    killer_q = select(
        Killmail.killer_address.label("address"),
        Killmail.killer_name.label("name"),
    ).where(Killmail.killer_name.ilike(pattern))

    victim_q = select(
        Killmail.victim_address.label("address"),
        Killmail.victim_name.label("name"),
    ).where(Killmail.victim_name.ilike(pattern))

    pilot_result = await db.execute(killer_q.union(victim_q).limit(10))
    seen_pilots: dict[str, SearchPilotResult] = {}
    for row in pilot_result.all():
        addr = row[0]
        if addr not in seen_pilots:
            seen_pilots[addr] = SearchPilotResult(address=addr, name=row[1])
        if len(seen_pilots) >= 5:
            break
    pilots = list(seen_pilots.values())

    killer_corp_q = select(
        Killmail.killer_corp_id.label("corp_id"),
        Killmail.killer_corp_name.label("corp_name"),
    ).where(
        Killmail.killer_corp_name.ilike(pattern),
        Killmail.killer_corp_id.is_not(None),
    )

    victim_corp_q = select(
        Killmail.victim_corp_id.label("corp_id"),
        Killmail.victim_corp_name.label("corp_name"),
    ).where(
        Killmail.victim_corp_name.ilike(pattern),
        Killmail.victim_corp_id.is_not(None),
    )

    corp_result = await db.execute(killer_corp_q.union(victim_corp_q).limit(10))
    seen_corps: dict[int, SearchCorpResult] = {}
    for row in corp_result.all():
        cid = row[0]
        if cid not in seen_corps:
            seen_corps[cid] = SearchCorpResult(corp_id=cid, corp_name=row[1])
        if len(seen_corps) >= 5:
            break
    corps = list(seen_corps.values())

    zone_result = await db.execute(
        select(OrbitalZone).where(OrbitalZone.name.ilike(pattern)).limit(5)
    )
    zones = [
        SearchZoneResult(zone_id=z.zone_id, name=z.name, id=z.id)
        for z in zone_result.scalars().all()
    ]

    return GlobalSearchResponse(pilots=pilots, corps=corps, zones=zones)
