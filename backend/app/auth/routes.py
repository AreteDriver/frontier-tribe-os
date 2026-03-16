"""Auth routes — FusionAuth SSO callback + dev login."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.auth.sso import (
    exchange_code,
    generate_dev_identity,
    get_authorize_url,
    get_userinfo,
)
from app.config import settings
from app.db.models import Member
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login():
    """Redirect user to EVE Frontier FusionAuth OAuth2."""
    if not settings.eve_frontier_client_id:
        raise HTTPException(
            status_code=501,
            detail="SSO not configured — set EVE_FRONTIER_CLIENT_ID and EVE_FRONTIER_CLIENT_SECRET",
        )
    url, state = await get_authorize_url()
    return RedirectResponse(url=url)


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Handle FusionAuth callback — exchange code, get userinfo, return JWT."""
    if not settings.eve_frontier_client_id:
        raise HTTPException(
            status_code=501,
            detail="SSO not configured — set EVE_FRONTIER_CLIENT_ID and EVE_FRONTIER_CLIENT_SECRET",
        )
    try:
        token_data = await exchange_code(code)
        user_info = await get_userinfo(token_data["access_token"])
    except Exception:
        raise HTTPException(status_code=400, detail="SSO verification failed")

    # FusionAuth userinfo returns sub (user ID), email, preferred_username, etc.
    # The wallet address is derived via zkLogin — for now use sub as identity
    wallet_address = user_info.get("sub", "")
    character_name = user_info.get("preferred_username") or user_info.get(
        "name", "Unknown"
    )

    if not wallet_address:
        raise HTTPException(
            status_code=400, detail="Could not extract identity from SSO response"
        )

    member = await _get_or_create_member(db, wallet_address, character_name)
    token = create_access_token(
        {"sub": member.wallet_address, "name": member.character_name}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "character_name": member.character_name,
    }


@router.post("/dev-login")
async def dev_login(
    name: str = Query("DevPilot"),
    db: AsyncSession = Depends(get_db),
):
    """Dev-only login that creates a mock identity. Disabled in production."""
    if settings.environment != "development":
        raise HTTPException(
            status_code=403, detail="Dev login not available in production"
        )

    identity = generate_dev_identity(name)
    member = await _get_or_create_member(
        db, identity["wallet_address"], identity["character_name"]
    )
    token = create_access_token(
        {"sub": member.wallet_address, "name": member.character_name}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "wallet_address": member.wallet_address,
        "character_name": member.character_name,
    }


async def _get_or_create_member(
    db: AsyncSession, wallet_address: str, character_name: str
) -> Member:
    result = await db.execute(
        select(Member).where(Member.wallet_address == wallet_address)
    )
    member = result.scalar_one_or_none()
    if not member:
        member = Member(wallet_address=wallet_address, character_name=character_name)
        db.add(member)
        await db.commit()
        await db.refresh(member)
    return member
