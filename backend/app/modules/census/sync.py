"""Sync tribe and member data from the EVE Frontier World API.

Pulls /v2/tribes and /v2/tribes/{id} to populate local records.
Local DB is the coordination layer (roles, jobs); World API is source of truth for membership.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.frontier import get_tribe as api_get_tribe
from app.api.frontier import get_tribes as api_get_tribes
from app.db.models import Member, Tribe

logger = logging.getLogger(__name__)


async def sync_all_tribes(db: AsyncSession) -> dict:
    """Sync all tribes from World API into local DB."""
    api_tribes = await api_get_tribes()
    created = 0
    updated = 0

    for t in api_tribes:
        world_id = t.get("id")
        if not world_id:
            continue

        existing = await db.scalar(
            select(Tribe).where(Tribe.world_tribe_id == world_id)
        )
        if existing:
            existing.name = t.get("name", existing.name)
            existing.name_short = t.get("nameShort", existing.name_short)
            updated += 1
        else:
            tribe = Tribe(
                world_tribe_id=world_id,
                name=t.get("name", "Unknown"),
                name_short=t.get("nameShort"),
            )
            db.add(tribe)
            created += 1

    await db.commit()
    return {"created": created, "updated": updated, "total": len(api_tribes)}


async def sync_tribe_members(db: AsyncSession, tribe_id: UUID) -> dict:
    """Sync members for a specific tribe from World API."""
    tribe = await db.get(Tribe, tribe_id)
    if not tribe or not tribe.world_tribe_id:
        return {"error": "Tribe not found or not linked to World API"}

    api_tribe = await api_get_tribe(str(tribe.world_tribe_id))
    if not api_tribe:
        return {"error": "Failed to fetch tribe from World API"}

    api_members = api_tribe.get("members", [])
    synced = 0
    new_members = 0

    for m in api_members:
        address = m.get("address", "")
        name = m.get("name", "")
        entity_id = str(m.get("id", ""))

        if not address or address == "0x0000000000000000000000000000000000000000":
            continue

        existing = await db.scalar(
            select(Member).where(Member.wallet_address == address)
        )
        if existing:
            existing.character_name = (
                name if name != "DEFAULT" else existing.character_name
            )
            existing.smart_character_id = entity_id
            if existing.tribe_id != tribe_id:
                existing.tribe_id = tribe_id
                existing.role = "member"  # Default on-chain members to "member" role
            synced += 1
        else:
            member = Member(
                tribe_id=tribe_id,
                wallet_address=address,
                character_name=name if name != "DEFAULT" else None,
                smart_character_id=entity_id,
                role="member",
            )
            db.add(member)
            new_members += 1

    await db.commit()
    return {
        "tribe": tribe.name,
        "api_member_count": len(api_members),
        "synced": synced,
        "new_members": new_members,
    }
