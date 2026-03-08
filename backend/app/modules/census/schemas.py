from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TribeCreate(BaseModel):
    name: str
    name_short: str | None = None


class TribeResponse(BaseModel):
    id: UUID
    name: str
    name_short: str | None
    invite_code: str | None
    created_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    id: UUID
    wallet_address: str
    character_name: str | None
    role: str
    timezone: str | None
    last_active: datetime | None
    joined_at: datetime

    model_config = {"from_attributes": True}


class RoleUpdate(BaseModel):
    role: str


class JoinRequestResponse(BaseModel):
    id: UUID
    wallet_address: str
    character_name: str | None
    status: str
    requested_at: datetime

    model_config = {"from_attributes": True}


class JoinRequestAction(BaseModel):
    action: str  # "approve" or "deny"
