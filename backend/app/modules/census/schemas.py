from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class TribeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    name_short: str | None = Field(None, max_length=10)


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
    ship_class: str | None = None
    timezone: str | None
    last_active: datetime | None
    joined_at: datetime
    is_active: bool = True

    model_config = {"from_attributes": True}


class RoleUpdate(BaseModel):
    role: Literal["leader", "officer", "member", "recruit"]


class JoinRequestResponse(BaseModel):
    id: UUID
    wallet_address: str
    character_name: str | None
    status: str
    requested_at: datetime

    model_config = {"from_attributes": True}


class JoinRequestAction(BaseModel):
    action: Literal["approve", "deny"]
