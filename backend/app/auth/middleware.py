from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.db.models import Member
from app.db.session import get_db

security = HTTPBearer()


async def get_current_member(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Member:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    wallet_address = payload.get("sub")
    if wallet_address is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    result = await db.execute(
        select(Member).where(Member.wallet_address == wallet_address)
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Member not found"
        )

    return member


async def require_role(
    required_roles: list[str], member: Member = Depends(get_current_member)
) -> Member:
    if member.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )
    return member


def require_leader_or_officer(member: Member = Depends(get_current_member)) -> Member:
    if member.role not in ("leader", "officer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Leader or officer role required",
        )
    return member
