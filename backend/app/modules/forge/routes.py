import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_member, require_leader_or_officer
from app.db.models import Member, ProductionJob, TribeInventory
from app.db.session import get_db

from .schemas import (
    GapAnalysisResponse,
    InventoryItem,
    InventoryResponse,
    JobCreate,
    JobResponse,
    JobUpdate,
    MaterialGap,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forge", tags=["forge"])

VALID_STATUSES = {"queued", "in_progress", "blocked", "complete"}

BLUEPRINTS_PATH = Path(__file__).resolve().parents[3] / "data" / "blueprints.json"

_blueprints_cache: list[dict] | None = None


def _load_blueprints() -> list[dict]:
    global _blueprints_cache
    if _blueprints_cache is None:
        try:
            _blueprints_cache = json.loads(BLUEPRINTS_PATH.read_text())
        except Exception:
            logger.warning(
                "Failed to load blueprints.json from %s, using empty list",
                BLUEPRINTS_PATH,
            )
            return []  # Don't cache failures
    return _blueprints_cache


@router.post(
    "/tribes/{tribe_id}/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    tribe_id: UUID,
    body: JobCreate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    job = ProductionJob(
        tribe_id=tribe_id,
        created_by=member.id,
        assigned_to=body.assigned_to,
        type_id=body.type_id,
        blueprint_name=body.blueprint_name,
        quantity=body.quantity,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return await _job_to_response(job, db)


@router.get("/tribes/{tribe_id}/jobs", response_model=list[JobResponse])
async def list_jobs(
    tribe_id: UUID,
    status_filter: str | None = None,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    query = select(ProductionJob).where(ProductionJob.tribe_id == tribe_id)
    if status_filter and status_filter in VALID_STATUSES:
        query = query.where(ProductionJob.status == status_filter)
    query = query.order_by(ProductionJob.created_at.desc())

    result = await db.execute(query)
    jobs = result.scalars().all()
    return [await _job_to_response(j, db) for j in jobs]


@router.patch("/tribes/{tribe_id}/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    tribe_id: UUID,
    job_id: UUID,
    body: JobUpdate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    job = await db.get(ProductionJob, job_id)
    if not job or job.tribe_id != tribe_id:
        raise HTTPException(status_code=404, detail="Job not found")

    if body.status is not None:
        if body.status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {VALID_STATUSES}",
            )
        job.status = body.status
        if body.status == "complete":
            job.completed_at = datetime.now(timezone.utc)

    if body.assigned_to is not None:
        job.assigned_to = body.assigned_to
    if body.materials_ready is not None:
        job.materials_ready = body.materials_ready

    await db.commit()
    await db.refresh(job)
    return await _job_to_response(job, db)


@router.delete(
    "/tribes/{tribe_id}/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_job(
    tribe_id: UUID,
    job_id: UUID,
    member: Member = Depends(require_leader_or_officer),
    db: AsyncSession = Depends(get_db),
):
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    job = await db.get(ProductionJob, job_id)
    if not job or job.tribe_id != tribe_id:
        raise HTTPException(status_code=404, detail="Job not found")

    await db.delete(job)
    await db.commit()


@router.get("/tribes/{tribe_id}/inventory", response_model=list[InventoryResponse])
async def list_inventory(
    tribe_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    result = await db.execute(
        select(TribeInventory)
        .where(TribeInventory.tribe_id == tribe_id)
        .order_by(TribeInventory.item_name)
    )
    return result.scalars().all()


@router.put("/tribes/{tribe_id}/inventory")
async def upsert_inventory(
    tribe_id: UUID,
    body: InventoryItem,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    existing = await db.scalar(
        select(TribeInventory).where(
            TribeInventory.tribe_id == tribe_id,
            TribeInventory.item_id == body.item_id,
        )
    )

    if existing:
        existing.quantity = body.quantity
        existing.item_name = body.item_name
        existing.updated_by = member.id
        existing.updated_at = datetime.now(timezone.utc)
    else:
        item = TribeInventory(
            tribe_id=tribe_id,
            item_id=body.item_id,
            item_name=body.item_name,
            quantity=body.quantity,
            updated_by=member.id,
        )
        db.add(item)

    await db.commit()
    return {"detail": "Inventory updated"}


@router.get("/tribes/{tribe_id}/gap-analysis", response_model=GapAnalysisResponse)
async def gap_analysis(
    tribe_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Compare required materials for active jobs vs tribe inventory."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    # Get active (non-complete) jobs
    result = await db.execute(
        select(ProductionJob).where(
            ProductionJob.tribe_id == tribe_id,
            ProductionJob.status.in_(["queued", "in_progress", "blocked"]),
        )
    )
    jobs = result.scalars().all()

    # Get tribe inventory
    inv_result = await db.execute(
        select(TribeInventory).where(TribeInventory.tribe_id == tribe_id)
    )
    inventory = {str(i.item_id): i.quantity for i in inv_result.scalars().all()}

    # Build material requirements from blueprints
    blueprints = _load_blueprints()
    bp_map = {bp["type_id"]: bp for bp in blueprints}

    required: dict[str, dict] = {}  # item_id -> {name, quantity}
    for job in jobs:
        bp_key = job.blueprint_name
        bp = bp_map.get(bp_key)
        if not bp:
            continue
        for mat in bp.get("materials", []):
            mid = mat["item_id"]
            if mid not in required:
                required[mid] = {"name": mat["name"], "quantity": 0}
            required[mid]["quantity"] += mat["quantity"] * job.quantity

    # Compute gaps
    gaps = []
    for item_id, info in sorted(required.items(), key=lambda x: x[1]["name"]):
        held = inventory.get(item_id, 0)
        deficit = max(0, info["quantity"] - held)
        if deficit > 0:
            gaps.append(
                MaterialGap(
                    item_id=item_id,
                    item_name=info["name"],
                    required=info["quantity"],
                    held=held,
                    deficit=deficit,
                )
            )

    return GapAnalysisResponse(
        total_jobs=len(jobs),
        jobs_materials_ready=sum(1 for j in jobs if j.materials_ready),
        jobs_blocked=sum(1 for j in jobs if j.status == "blocked"),
        material_gaps=gaps,
    )


@router.get("/blueprints")
async def list_blueprints(
    member: Member = Depends(get_current_member),
):
    """Return available blueprints with material requirements."""
    return _load_blueprints()


async def _job_to_response(job: ProductionJob, db: AsyncSession) -> JobResponse:
    assigned_name = None
    if job.assigned_to:
        assigned = await db.get(Member, job.assigned_to)
        if assigned:
            assigned_name = assigned.character_name

    return JobResponse(
        id=job.id,
        type_id=job.type_id,
        blueprint_name=job.blueprint_name,
        quantity=job.quantity,
        status=job.status,
        materials_ready=job.materials_ready,
        assigned_to=job.assigned_to,
        assigned_name=assigned_name,
        created_by=job.created_by,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
