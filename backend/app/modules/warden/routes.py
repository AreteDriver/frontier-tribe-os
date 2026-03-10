"""Warden module — autonomous defense intelligence for tribe security."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_member, require_leader_or_officer
from app.db.models import Member, Tribe
from app.db.session import get_db

from .schemas import (
    WardenAlertResponse,
    WardenConfigUpdate,
    WardenStatusResponse,
)

router = APIRouter(prefix="/warden", tags=["warden"])

# In-memory engine registry (one per tribe)
# Production: move to Redis or DB-backed state
_engines: dict[str, "WardenEngine"] = {}  # noqa: F821


def _get_engine(tribe_id: str):
    """Get or lazily reference a warden engine for a tribe."""
    return _engines.get(tribe_id)


@router.get("/status")
async def warden_status():
    """Health check for the warden module."""
    return {
        "status": "ok",
        "active_wardens": len(_engines),
        "tribes_monitored": list(_engines.keys()),
    }


@router.get("/tribes/{tribe_id}/status", response_model=WardenStatusResponse)
async def get_tribe_warden_status(
    tribe_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get the warden status for a specific tribe."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    tribe = await db.get(Tribe, tribe_id)
    if not tribe:
        raise HTTPException(status_code=404, detail="Tribe not found")

    engine = _get_engine(str(tribe_id))
    if engine:
        data = engine.status()
        return WardenStatusResponse(**data)

    return WardenStatusResponse(
        tribe_id=tribe_id,
        enabled=False,
        running=False,
        total_cycles=0,
        total_alerts=0,
        unacknowledged_alerts=0,
        last_cycle_at=None,
        doctrine_loaded=False,
    )


@router.post("/tribes/{tribe_id}/enable")
async def enable_warden(
    tribe_id: UUID,
    config: WardenConfigUpdate | None = None,
    member: Member = Depends(require_leader_or_officer),
    db: AsyncSession = Depends(get_db),
):
    """Enable the warden for a tribe. Leader/officer only."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    tribe = await db.get(Tribe, tribe_id)
    if not tribe:
        raise HTTPException(status_code=404, detail="Tribe not found")

    if not tribe.leader_address:
        raise HTTPException(status_code=400, detail="Tribe has no treasury address to monitor")

    from .engine import WardenEngine

    tid = str(tribe_id)
    if tid in _engines:
        return {"status": "already_enabled", "tribe_id": tid}

    engine = WardenEngine(
        tribe_id=tid,
        tribe_address=tribe.leader_address,
        max_cycles=config.max_cycles_per_session if config and config.max_cycles_per_session else 24,
        alert_tier_threshold=config.alert_tier_threshold if config and config.alert_tier_threshold else 2,
        cycle_interval_seconds=config.cycle_interval_seconds if config and config.cycle_interval_seconds else 300,
    )
    engine.load_doctrine()
    _engines[tid] = engine

    return {"status": "enabled", "tribe_id": tid}


@router.post("/tribes/{tribe_id}/disable")
async def disable_warden(
    tribe_id: UUID,
    member: Member = Depends(require_leader_or_officer),
):
    """Disable the warden for a tribe. Leader/officer only."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    tid = str(tribe_id)
    engine = _engines.pop(tid, None)
    if engine:
        engine.stop()
        return {"status": "disabled", "tribe_id": tid, "cycles_completed": engine.cycle_count}

    return {"status": "not_enabled", "tribe_id": tid}


@router.post("/tribes/{tribe_id}/cycle")
async def run_single_cycle(
    tribe_id: UUID,
    member: Member = Depends(require_leader_or_officer),
):
    """Run a single defense cycle manually. Leader/officer only."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    tid = str(tribe_id)
    engine = _get_engine(tid)
    if not engine:
        raise HTTPException(status_code=400, detail="Warden not enabled for this tribe")

    record = await engine.run_cycle()
    return record.model_dump()


@router.get("/tribes/{tribe_id}/alerts", response_model=WardenAlertResponse)
async def list_alerts(
    tribe_id: UUID,
    member: Member = Depends(get_current_member),
):
    """List warden alerts for a tribe."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    tid = str(tribe_id)
    engine = _get_engine(tid)
    if not engine:
        return WardenAlertResponse(alerts=[])

    return WardenAlertResponse(alerts=engine.alerts)


@router.post("/tribes/{tribe_id}/alerts/{alert_index}/acknowledge")
async def acknowledge_alert(
    tribe_id: UUID,
    alert_index: int,
    member: Member = Depends(require_leader_or_officer),
):
    """Acknowledge a warden alert. Leader/officer only."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    tid = str(tribe_id)
    engine = _get_engine(tid)
    if not engine:
        raise HTTPException(status_code=400, detail="Warden not enabled")

    if alert_index < 0 or alert_index >= len(engine.alerts):
        raise HTTPException(status_code=404, detail="Alert not found")

    engine.alerts[alert_index]["acknowledged"] = True
    return {"status": "acknowledged", "alert_index": alert_index}


@router.post("/tribes/{tribe_id}/doctrine")
async def update_doctrine(
    tribe_id: UUID,
    doctrine_text: str,
    member: Member = Depends(require_leader_or_officer),
):
    """Update the warden doctrine for a tribe. Leader/officer only."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    if not doctrine_text.strip():
        raise HTTPException(status_code=400, detail="Doctrine cannot be empty")

    tid = str(tribe_id)
    engine = _get_engine(tid)
    if not engine:
        raise HTTPException(status_code=400, detail="Warden not enabled")

    engine.load_doctrine(doctrine_text)
    return {"status": "doctrine_updated", "length": len(doctrine_text)}
