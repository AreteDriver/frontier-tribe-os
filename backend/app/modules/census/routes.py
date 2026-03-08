import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_member, require_leader_or_officer
from app.modules.census.sync import sync_all_tribes, sync_tribe_members
from app.db.models import JoinRequest, Member, Tribe
from app.db.session import get_db

from .schemas import (
    JoinRequestAction,
    JoinRequestResponse,
    MemberResponse,
    RoleUpdate,
    TribeCreate,
    TribeResponse,
)

router = APIRouter(prefix="/census", tags=["census"])

VALID_ROLES = {"leader", "officer", "member", "recruit"}


@router.post("/tribes", response_model=TribeResponse, status_code=status.HTTP_201_CREATED)
async def create_tribe(
    body: TribeCreate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tribe. The creating member becomes the leader."""
    if member.tribe_id is not None:
        # Check if already in a tribe — for now, one tribe per member
        existing = await db.get(Tribe, member.tribe_id)
        if existing:
            raise HTTPException(status_code=400, detail="You are already in a tribe")

    tribe = Tribe(
        name=body.name,
        name_short=body.name_short,
        leader_address=member.wallet_address,
        invite_code=secrets.token_urlsafe(16),
    )
    db.add(tribe)
    await db.flush()

    # Update member to belong to this tribe as leader
    member.tribe_id = tribe.id
    member.role = "leader"
    await db.commit()
    await db.refresh(tribe)

    return TribeResponse(
        id=tribe.id,
        name=tribe.name,
        name_short=tribe.name_short,
        invite_code=tribe.invite_code,
        created_at=tribe.created_at,
        member_count=1,
    )


@router.get("/tribes/{tribe_id}", response_model=TribeResponse)
async def get_tribe(
    tribe_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    tribe = await db.get(Tribe, tribe_id)
    if not tribe:
        raise HTTPException(status_code=404, detail="Tribe not found")

    count = await db.scalar(select(func.count()).where(Member.tribe_id == tribe_id))

    return TribeResponse(
        id=tribe.id,
        name=tribe.name,
        name_short=tribe.name_short,
        invite_code=tribe.invite_code if member.tribe_id == tribe_id else None,
        created_at=tribe.created_at,
        member_count=count or 0,
    )


@router.get("/tribes/{tribe_id}/members", response_model=list[MemberResponse])
async def list_members(
    tribe_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    result = await db.execute(
        select(Member).where(Member.tribe_id == tribe_id).order_by(Member.joined_at)
    )
    return result.scalars().all()


@router.post("/tribes/join/{invite_code}", status_code=status.HTTP_201_CREATED)
async def request_join(
    invite_code: str,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Submit a join request to a tribe via invite code."""
    tribe = await db.scalar(select(Tribe).where(Tribe.invite_code == invite_code))
    if not tribe:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    # Check for existing pending request
    existing = await db.scalar(
        select(JoinRequest).where(
            JoinRequest.tribe_id == tribe.id,
            JoinRequest.wallet_address == member.wallet_address,
            JoinRequest.status == "pending",
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="Join request already pending")

    request = JoinRequest(
        tribe_id=tribe.id,
        wallet_address=member.wallet_address,
        character_name=member.character_name,
    )
    db.add(request)
    await db.commit()
    return {"detail": "Join request submitted", "tribe_name": tribe.name}


@router.get("/tribes/{tribe_id}/requests", response_model=list[JoinRequestResponse])
async def list_join_requests(
    tribe_id: UUID,
    member: Member = Depends(require_leader_or_officer),
    db: AsyncSession = Depends(get_db),
):
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    result = await db.execute(
        select(JoinRequest).where(JoinRequest.tribe_id == tribe_id, JoinRequest.status == "pending")
    )
    return result.scalars().all()


@router.post("/tribes/{tribe_id}/requests/{request_id}")
async def handle_join_request(
    tribe_id: UUID,
    request_id: UUID,
    body: JoinRequestAction,
    member: Member = Depends(require_leader_or_officer),
    db: AsyncSession = Depends(get_db),
):
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    if body.action not in ("approve", "deny"):
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'deny'")

    join_req = await db.get(JoinRequest, request_id)
    if not join_req or join_req.tribe_id != tribe_id:
        raise HTTPException(status_code=404, detail="Join request not found")

    if join_req.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    join_req.status = "approved" if body.action == "approve" else "denied"

    if body.action == "approve":
        # Find or create member record for this character
        existing_member = await db.scalar(
            select(Member).where(Member.wallet_address == join_req.wallet_address)
        )
        if existing_member:
            existing_member.tribe_id = tribe_id
            existing_member.role = "recruit"
            existing_member.joined_at = datetime.now(timezone.utc)
        else:
            new_member = Member(
                tribe_id=tribe_id,
                wallet_address=join_req.wallet_address,
                character_name=join_req.character_name,
                role="recruit",
            )
            db.add(new_member)

    await db.commit()
    return {"detail": f"Request {body.action}d"}


@router.patch("/tribes/{tribe_id}/members/{member_id}/role")
async def update_member_role(
    tribe_id: UUID,
    member_id: UUID,
    body: RoleUpdate,
    member: Member = Depends(require_leader_or_officer),
    db: AsyncSession = Depends(get_db),
):
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {VALID_ROLES}")

    # Only leaders can promote to officer
    if body.role == "officer" and member.role != "leader":
        raise HTTPException(status_code=403, detail="Only leaders can promote to officer")

    target = await db.get(Member, member_id)
    if not target or target.tribe_id != tribe_id:
        raise HTTPException(status_code=404, detail="Member not found in this tribe")

    # Can't demote the leader
    if target.role == "leader" and body.role != "leader":
        raise HTTPException(status_code=400, detail="Cannot demote the tribe leader")

    target.role = body.role
    await db.commit()
    return {"detail": f"Role updated to {body.role}"}


@router.post("/sync/tribes")
async def sync_tribes(
    member: Member = Depends(require_leader_or_officer),
    db: AsyncSession = Depends(get_db),
):
    """Pull all tribes from World API into local DB."""
    result = await sync_all_tribes(db)
    return result


@router.post("/sync/tribes/{tribe_id}/members")
async def sync_members(
    tribe_id: UUID,
    member: Member = Depends(require_leader_or_officer),
    db: AsyncSession = Depends(get_db),
):
    """Sync members for a specific tribe from World API."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")
    result = await sync_tribe_members(db, tribe_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
