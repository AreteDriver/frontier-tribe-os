"""Ledger module — Sui token treasury, balances, and transaction history."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import sui
from app.auth.middleware import get_current_member, require_leader_or_officer
from app.db.models import LedgerTransaction, Member, Tribe
from app.db.session import get_db

from .schemas import (
    BalanceResponse,
    MemberBalance,
    TransactionResponse,
    TransferRecord,
    TreasurySummary,
    WalletBalancesResponse,
)

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("/status")
async def ledger_status():
    return {"status": "ok"}


@router.get("/tribes/{tribe_id}/balances", response_model=WalletBalancesResponse)
async def get_tribe_balances(
    tribe_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get on-chain balances for the tribe treasury (leader wallet)."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    tribe = await db.get(Tribe, tribe_id)
    if not tribe:
        raise HTTPException(status_code=404, detail="Tribe not found")

    address = tribe.leader_address
    if not address:
        raise HTTPException(status_code=400, detail="Tribe has no treasury address")

    raw_balances = await sui.get_all_balances(address)
    balances = [
        BalanceResponse(
            coin_type=b.get("coinType", "unknown"),
            total_balance=str(b.get("totalBalance", "0")),
            coin_object_count=b.get("coinObjectCount", 0),
        )
        for b in raw_balances
    ]
    return WalletBalancesResponse(address=address, balances=balances)


@router.get("/members/me/balances", response_model=WalletBalancesResponse)
async def get_my_balances(
    member: Member = Depends(get_current_member),
):
    """Get on-chain balances for the current member's wallet."""
    raw_balances = await sui.get_all_balances(member.wallet_address)
    balances = [
        BalanceResponse(
            coin_type=b.get("coinType", "unknown"),
            total_balance=str(b.get("totalBalance", "0")),
            coin_object_count=b.get("coinObjectCount", 0),
        )
        for b in raw_balances
    ]
    return WalletBalancesResponse(address=member.wallet_address, balances=balances)


@router.get("/tribes/{tribe_id}/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    tribe_id: UUID,
    limit: int = 50,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """List recorded transactions for this tribe."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    result = await db.execute(
        select(LedgerTransaction)
        .where(LedgerTransaction.tribe_id == tribe_id)
        .order_by(LedgerTransaction.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post(
    "/tribes/{tribe_id}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_transaction(
    tribe_id: UUID,
    body: TransferRecord,
    member: Member = Depends(require_leader_or_officer),
    db: AsyncSession = Depends(get_db),
):
    """Record a completed on-chain transaction. Called after frontend signs + executes tx."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    # Check for duplicate tx_digest
    existing = await db.scalar(
        select(LedgerTransaction).where(LedgerTransaction.tx_digest == body.tx_digest)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Transaction already recorded")

    tx = LedgerTransaction(
        tribe_id=tribe_id,
        tx_digest=body.tx_digest,
        from_address=member.wallet_address,
        to_address=body.to_address,
        amount=body.amount,
        coin_type=body.coin_type,
        memo=body.memo,
        status="confirmed",
        created_by=member.id,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


@router.get(
    "/tribes/{tribe_id}/members/{member_id}/balances",
    response_model=WalletBalancesResponse,
)
async def get_member_balances(
    tribe_id: UUID,
    member_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Get on-chain balances for a specific tribe member."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    target = await db.get(Member, member_id)
    if not target or target.tribe_id != tribe_id:
        raise HTTPException(status_code=404, detail="Member not found in this tribe")

    raw_balances = await sui.get_all_balances(target.wallet_address)
    balances = [
        BalanceResponse(
            coin_type=b.get("coinType", "unknown"),
            total_balance=str(b.get("totalBalance", "0")),
            coin_object_count=b.get("coinObjectCount", 0),
        )
        for b in raw_balances
    ]
    return WalletBalancesResponse(address=target.wallet_address, balances=balances)


logger = logging.getLogger(__name__)


@router.get("/tribes/{tribe_id}/summary", response_model=TreasurySummary)
async def get_treasury_summary(
    tribe_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate treasury view: tribe balances, member count, tx count."""
    if member.tribe_id != tribe_id:
        raise HTTPException(status_code=403, detail="Not a member of this tribe")

    tribe = await db.get(Tribe, tribe_id)
    if not tribe:
        raise HTTPException(status_code=404, detail="Tribe not found")

    # Treasury balances
    treasury_balances = []
    if tribe.leader_address:
        try:
            raw = await sui.get_all_balances(tribe.leader_address)
            treasury_balances = [
                BalanceResponse(
                    coin_type=b.get("coinType", "unknown"),
                    total_balance=str(b.get("totalBalance", "0")),
                    coin_object_count=b.get("coinObjectCount", 0),
                )
                for b in raw
            ]
        except Exception:
            logger.warning("Failed to fetch treasury balances for tribe %s", tribe_id)

    # Member count
    member_count = (
        await db.scalar(select(func.count()).where(Member.tribe_id == tribe_id)) or 0
    )

    # Transaction count
    tx_count = (
        await db.scalar(
            select(func.count()).where(LedgerTransaction.tribe_id == tribe_id)
        )
        or 0
    )

    # Member balances (best-effort, skip failures)
    members_result = await db.execute(select(Member).where(Member.tribe_id == tribe_id))
    members_with_balances = []
    for m in members_result.scalars().all():
        try:
            raw = await sui.get_all_balances(m.wallet_address)
            balances = [
                BalanceResponse(
                    coin_type=b.get("coinType", "unknown"),
                    total_balance=str(b.get("totalBalance", "0")),
                    coin_object_count=b.get("coinObjectCount", 0),
                )
                for b in raw
            ]
            members_with_balances.append(
                MemberBalance(
                    member_id=m.id,
                    character_name=m.character_name,
                    role=m.role,
                    address=m.wallet_address,
                    balances=balances,
                )
            )
        except Exception:
            logger.warning("Failed to fetch balances for member %s", m.id)

    return TreasurySummary(
        tribe_name=tribe.name,
        treasury_address=tribe.leader_address,
        treasury_balances=treasury_balances,
        member_count=member_count,
        total_transactions=tx_count,
        members_with_balances=members_with_balances,
    )
