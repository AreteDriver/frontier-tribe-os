"""Watch module schemas — C5 orbital zones, scans, clones, crowns."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# --- Cycle ---


class CycleResponse(BaseModel):
    cycle: int
    cycle_name: str
    reset_at: str
    days_elapsed: int


# --- Orbital Zones ---


class OrbitalZoneResponse(BaseModel):
    id: UUID
    zone_id: str
    name: str
    feral_ai_tier: int
    threat_level: str  # Derived: DORMANT / ACTIVE / EVOLVED / CRITICAL
    last_scanned: datetime | None
    scan_stale: bool  # True if >15 min since last scan
    created_at: datetime

    model_config = {"from_attributes": True}


class OrbitalZoneCreate(BaseModel):
    zone_id: str
    name: str
    coordinates: str | None = None
    feral_ai_tier: int = 0


class FeralAIEventResponse(BaseModel):
    id: UUID
    event_type: str
    severity: int
    previous_tier: int | None
    new_tier: int | None
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- Scans ---


class ScanCreate(BaseModel):
    zone_id: UUID
    result_type: str  # CLEAR, ANOMALY, HOSTILE, UNKNOWN
    result_data: str | None = None
    confidence: int = 100


class ScanResponse(BaseModel):
    id: UUID
    zone_id: UUID
    scanner_id: UUID | None
    result_type: str
    confidence: int
    scanned_at: datetime

    model_config = {"from_attributes": True}


# --- Clones ---


class CloneResponse(BaseModel):
    id: UUID
    clone_id: str
    owner_id: UUID | None
    blueprint_id: str | None
    status: str
    manufactured_at: datetime | None

    model_config = {"from_attributes": True}


class CloneQueueResponse(BaseModel):
    total_active: int
    total_manufacturing: int
    low_reserve: bool
    reserve_threshold: int
    clones: list[CloneResponse]


# --- Crowns ---


class CrownResponse(BaseModel):
    id: UUID
    crown_id: str
    character_id: UUID | None
    crown_type: str
    equipped_at: datetime | None

    model_config = {"from_attributes": True}


class CrownRosterResponse(BaseModel):
    total_members: int
    members_with_crowns: int
    members_without_crowns: int
    crown_type_distribution: dict[str, int]
    crowns: list[CrownResponse]
