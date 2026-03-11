"""Watch module — C5 cycle tracking, orbital zones, scans, clones, crowns."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_member
from app.config import settings
from app.db.models import (
    CURRENT_CYCLE,
    Clone,
    Crown,
    FeralAIEvent,
    Member,
    OrbitalZone,
    Scan,
)
from app.db.session import get_db
from app.notifications.notifier import DiscordNotifier

from .schemas import (
    CloneQueueResponse,
    CloneResponse,
    CrownResponse,
    CrownRosterResponse,
    CycleResponse,
    FeralAIEventResponse,
    OrbitalZoneCreate,
    OrbitalZoneResponse,
    ScanCreate,
    ScanResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/watch", tags=["watch"])


def _get_notifier() -> DiscordNotifier:
    return DiscordNotifier(
        webhook_url=settings.discord_webhook_url,
        dry_run=not settings.discord_webhook_url,
    )


# C5 reset timestamp — update when cycle starts
CYCLE_RESET_AT = "2026-03-11T00:00:00Z"
CYCLE_NAME = "Shroud of Fear"

THREAT_LEVELS = {0: "DORMANT", 1: "ACTIVE", 2: "EVOLVED", 3: "CRITICAL", 4: "CRITICAL"}
VALID_SCAN_RESULTS = {"CLEAR", "ANOMALY", "HOSTILE", "UNKNOWN"}
VALID_SIGNATURE_TYPES = {"EM", "HEAT", "GRAVIMETRIC", "RADAR", "UNKNOWN"}
SCAN_STALE_MINUTES = 15
CLONE_RESERVE_THRESHOLD = 5


def _threat_level(tier: int) -> str:
    return THREAT_LEVELS.get(tier, "CRITICAL" if tier >= 3 else "DORMANT")


def _resolution_label(resolution: int) -> str:
    """Graduated visibility label from resolution percentage."""
    if resolution >= 75:
        return "FULL_INTEL"
    if resolution >= 50:
        return "IDENTIFIED"
    if resolution >= 25:
        return "PARTIAL"
    return "UNRESOLVED"


def _scan_to_response(scan: Scan) -> ScanResponse:
    """Convert a Scan model to ScanResponse with computed fields."""
    return ScanResponse(
        id=scan.id,
        zone_id=scan.zone_id,
        scanner_id=scan.scanner_id,
        result_type=scan.result_type,
        signature_type=scan.signature_type,
        resolution=scan.resolution,
        resolution_label=_resolution_label(scan.resolution),
        confidence=scan.confidence,
        environment=scan.environment,
        scanned_at=scan.scanned_at,
    )


def _is_scan_stale(last_scanned: datetime | None) -> bool:
    if not last_scanned:
        return True
    now = datetime.now(timezone.utc)
    last = (
        last_scanned.replace(tzinfo=timezone.utc)
        if last_scanned.tzinfo is None
        else last_scanned
    )
    return (now - last) > timedelta(minutes=SCAN_STALE_MINUTES)


# --- Cycle ---


@router.get("/cycle", response_model=CycleResponse)
async def get_cycle():
    """Return current cycle info."""
    reset = datetime.fromisoformat(CYCLE_RESET_AT.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    days = (now - reset).days
    return CycleResponse(
        cycle=CURRENT_CYCLE,
        cycle_name=CYCLE_NAME,
        reset_at=CYCLE_RESET_AT,
        days_elapsed=max(0, days),
    )


# --- Orbital Zones ---


@router.get("/orbital-zones", response_model=list[OrbitalZoneResponse])
async def list_orbital_zones(
    threat_level: str | None = Query(None),
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """List orbital zones, optionally filtered by threat level."""
    query = select(OrbitalZone).where(OrbitalZone.cycle == CURRENT_CYCLE)
    result = await db.execute(query.order_by(OrbitalZone.feral_ai_tier.desc()))
    zones = result.scalars().all()

    responses = []
    for z in zones:
        tl = _threat_level(z.feral_ai_tier)
        if threat_level and tl != threat_level.upper():
            continue
        responses.append(
            OrbitalZoneResponse(
                id=z.id,
                zone_id=z.zone_id,
                name=z.name,
                feral_ai_tier=z.feral_ai_tier,
                threat_level=tl,
                last_scanned=z.last_scanned,
                scan_stale=_is_scan_stale(z.last_scanned),
                created_at=z.created_at,
            )
        )
    return responses


@router.post(
    "/orbital-zones",
    response_model=OrbitalZoneResponse,
    status_code=201,
)
async def create_orbital_zone(
    body: OrbitalZoneCreate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Create or update an orbital zone."""
    existing = await db.scalar(
        select(OrbitalZone).where(OrbitalZone.zone_id == body.zone_id)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Zone already exists")

    zone = OrbitalZone(
        zone_id=body.zone_id,
        name=body.name,
        coordinates_hash=body.coordinates_hash,
        feral_ai_tier=body.feral_ai_tier,
    )
    db.add(zone)
    await db.commit()
    await db.refresh(zone)

    return OrbitalZoneResponse(
        id=zone.id,
        zone_id=zone.zone_id,
        name=zone.name,
        feral_ai_tier=zone.feral_ai_tier,
        threat_level=_threat_level(zone.feral_ai_tier),
        last_scanned=zone.last_scanned,
        scan_stale=True,
        created_at=zone.created_at,
    )


@router.get(
    "/orbital-zones/{zone_id}/history",
    response_model=list[FeralAIEventResponse],
)
async def zone_history(
    zone_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get feral AI event history for a zone."""
    result = await db.execute(
        select(FeralAIEvent)
        .where(FeralAIEvent.zone_id == zone_id)
        .order_by(FeralAIEvent.timestamp.desc())
        .limit(50)
    )
    return result.scalars().all()


# --- Scans ---


@router.post("/scans", response_model=ScanResponse, status_code=201)
async def submit_scan(
    body: ScanCreate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Submit a void scan result."""
    if body.result_type not in VALID_SCAN_RESULTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid result_type. Must be one of: {VALID_SCAN_RESULTS}",
        )

    if body.signature_type and body.signature_type not in VALID_SIGNATURE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid signature_type. Must be one of: {VALID_SIGNATURE_TYPES}",
        )

    # Verify zone exists
    zone = await db.get(OrbitalZone, body.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    scan = Scan(
        zone_id=body.zone_id,
        scanner_id=member.id,
        result_type=body.result_type,
        signature_type=body.signature_type,
        resolution=body.resolution,
        result_data=body.result_data,
        confidence=body.confidence,
        environment=body.environment,
    )
    db.add(scan)

    # Update zone last_scanned
    zone.last_scanned = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(scan)

    # Fire Discord alert on HOSTILE scan
    if body.result_type == "HOSTILE":
        notifier = _get_notifier()
        scanner_name = member.character_name or "Unknown"
        await notifier.hostile_scan(zone=zone.name, scanner=scanner_name)

    return _scan_to_response(scan)


@router.get("/scans/feed", response_model=list[ScanResponse])
async def scan_feed(
    zone_id: UUID | None = Query(None),
    since: datetime | None = Query(None),
    limit: int = Query(50, le=200),
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Live feed of recent scans."""
    query = select(Scan).where(Scan.cycle == CURRENT_CYCLE)
    if zone_id:
        query = query.where(Scan.zone_id == zone_id)
    if since:
        query = query.where(Scan.scanned_at >= since)
    query = query.order_by(Scan.scanned_at.desc()).limit(limit)

    result = await db.execute(query)
    return [_scan_to_response(s) for s in result.scalars().all()]


# --- Clones ---


@router.get("/clones", response_model=CloneQueueResponse)
async def list_clones(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get clone status for the current member's tribe."""
    if not member.tribe_id:
        raise HTTPException(status_code=400, detail="Not in a tribe")

    # Get all tribe member IDs
    members_result = await db.execute(
        select(Member.id).where(Member.tribe_id == member.tribe_id)
    )
    member_ids = [m for m in members_result.scalars().all()]

    query = select(Clone).where(
        Clone.owner_id.in_(member_ids),
        Clone.cycle == CURRENT_CYCLE,
    )
    result = await db.execute(query)
    clones = result.scalars().all()

    active = [c for c in clones if c.status == "active"]
    manufacturing = [c for c in clones if c.status == "manufacturing"]

    return CloneQueueResponse(
        total_active=len(active),
        total_manufacturing=len(manufacturing),
        low_reserve=len(active) < CLONE_RESERVE_THRESHOLD,
        reserve_threshold=CLONE_RESERVE_THRESHOLD,
        clones=[CloneResponse.model_validate(c) for c in clones],
    )


# --- Crowns ---


@router.get("/crowns/roster", response_model=CrownRosterResponse)
async def crown_roster(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get crown roster for the current member's tribe."""
    if not member.tribe_id:
        raise HTTPException(status_code=400, detail="Not in a tribe")

    member_count = (
        await db.scalar(select(func.count()).where(Member.tribe_id == member.tribe_id))
        or 0
    )

    # Get tribe member IDs
    members_result = await db.execute(
        select(Member.id).where(Member.tribe_id == member.tribe_id)
    )
    member_ids = [m for m in members_result.scalars().all()]

    # Get crowns for tribe members
    result = await db.execute(
        select(Crown).where(
            Crown.character_id.in_(member_ids),
            Crown.cycle == CURRENT_CYCLE,
        )
    )
    crowns = result.scalars().all()

    # Crown type distribution
    distribution: dict[str, int] = {}
    members_with = set()
    for c in crowns:
        distribution[c.crown_type] = distribution.get(c.crown_type, 0) + 1
        if c.character_id:
            members_with.add(c.character_id)

    return CrownRosterResponse(
        total_members=member_count,
        members_with_crowns=len(members_with),
        members_without_crowns=member_count - len(members_with),
        crown_type_distribution=distribution,
        crowns=[CrownResponse.model_validate(c) for c in crowns],
    )


# --- Alerts ---

BLIND_SPOT_MINUTES = 20


@router.get("/alerts/blind-spots")
async def check_blind_spots(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Check for zones not scanned in >20 min and fire alerts."""
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(minutes=BLIND_SPOT_MINUTES)

    result = await db.execute(
        select(OrbitalZone).where(OrbitalZone.cycle == CURRENT_CYCLE)
    )
    zones = result.scalars().all()

    blind_spots = []
    notifier = _get_notifier()
    for z in zones:
        last = z.last_scanned
        if last is None or (
            (last.replace(tzinfo=timezone.utc) if last.tzinfo is None else last)
            < threshold
        ):
            minutes = (
                int((now - last.replace(tzinfo=timezone.utc)).total_seconds() / 60)
                if last
                else 999
            )
            blind_spots.append(
                {"zone_id": z.zone_id, "name": z.name, "unseen_minutes": minutes}
            )
            await notifier.blind_spot(zone=z.name, minutes=minutes)

    return {"blind_spots": blind_spots, "count": len(blind_spots)}


@router.post("/alerts/test")
async def test_alert(
    member: Member = Depends(get_current_member),
):
    """Send a test alert to verify Discord webhook is configured."""
    notifier = _get_notifier()
    sent = await notifier.send_alert("feral_ai_evolved", zone="Test Zone", tier=1)
    return {
        "sent": sent,
        "dry_run": notifier.dry_run,
        "webhook_configured": bool(settings.discord_webhook_url),
    }
