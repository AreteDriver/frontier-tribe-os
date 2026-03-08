"""Auth routes — SSO callback + dev login."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.auth.sso import exchange_code, generate_dev_identity, get_authorize_url, verify_token
from app.config import settings
from app.db.models import Member
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login():
    """Redirect user to EVE Frontier SSO."""
    url, state = await get_authorize_url()
    return {"authorize_url": url, "state": state}


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Handle SSO callback — exchange code, create/update member, return JWT."""
    try:
        token_data = await exchange_code(code)
        char_info = await verify_token(token_data["access_token"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SSO verification failed: {e}")

    character_id = str(char_info.get("CharacterID") or char_info.get("character_id", ""))
    character_name = char_info.get("CharacterName") or char_info.get("character_name", "Unknown")

    if not character_id:
        raise HTTPException(status_code=400, detail="Could not extract character ID from SSO response")

    member = await _get_or_create_member(db, character_id, character_name)
    token = create_access_token({"sub": member.character_id, "name": member.character_name})
    return {"access_token": token, "token_type": "bearer", "character_name": member.character_name}


@router.post("/dev-login")
async def dev_login(
    name: str = Query("DevPilot"),
    db: AsyncSession = Depends(get_db),
):
    """Dev-only login that creates a mock identity. Disabled in production."""
    if settings.environment != "development":
        raise HTTPException(status_code=403, detail="Dev login not available in production")

    identity = generate_dev_identity(name)
    member = await _get_or_create_member(db, identity["character_id"], identity["character_name"])
    token = create_access_token({"sub": member.character_id, "name": member.character_name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "character_id": member.character_id,
        "character_name": member.character_name,
    }


async def _get_or_create_member(db: AsyncSession, character_id: str, character_name: str) -> Member:
    result = await db.execute(select(Member).where(Member.character_id == character_id))
    member = result.scalar_one_or_none()
    if not member:
        member = Member(character_id=character_id, character_name=character_name)
        db.add(member)
        await db.commit()
        await db.refresh(member)
    return member
