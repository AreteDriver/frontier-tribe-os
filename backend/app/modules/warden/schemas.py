"""Pydantic schemas for the Warden module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ThreatHypothesis(BaseModel):
    """A generated threat hypothesis from blockchain event analysis."""

    threat_type: str = Field(..., description="Category: treasury_drain, hostile_transfer, smart_assembly_attack, unknown")
    hypothesis: str = Field(..., description="Specific, testable threat description")
    evidence: list[str] = Field(default_factory=list, description="Supporting blockchain events")
    estimated_severity: int = Field(..., ge=1, le=5, description="1=noise, 5=critical")
    suggested_response: str = Field(default="", description="Recommended action")


class ThreatEvaluation(BaseModel):
    """Evaluation of a threat hypothesis against warden doctrine."""

    outcome: str = Field(..., description="escalate|monitor|dismiss")
    tier: int = Field(..., ge=1, le=4, description="Response tier: 1=log, 2=alert, 3=operator-required, 4=emergency")
    rationale: str = Field(..., description="Why this outcome")
    confidence: float = Field(..., ge=0.0, le=1.0)


class WardenCycleRecord(BaseModel):
    """Single defense cycle result for audit log."""

    cycle: int
    tribe_id: str
    hypothesis: str
    threat_type: str
    severity: int
    evaluation_outcome: str
    tier: int
    rationale: str
    events_ingested: int
    timestamp: str


class WardenAlert(BaseModel):
    """Alert generated when a threat exceeds the configured tier threshold."""

    id: UUID | None = None
    tribe_id: UUID
    cycle: int
    threat_type: str
    severity: int
    tier: int
    hypothesis: str
    rationale: str
    acknowledged: bool = False
    created_at: datetime | None = None


class WardenStatusResponse(BaseModel):
    """Current warden status for a tribe."""

    tribe_id: UUID
    enabled: bool
    running: bool
    total_cycles: int
    total_alerts: int
    unacknowledged_alerts: int
    last_cycle_at: str | None = None
    doctrine_loaded: bool


class WardenAlertResponse(BaseModel):
    """Alert list response."""

    alerts: list[WardenAlert]


class WardenConfigUpdate(BaseModel):
    """Configuration update for warden settings."""

    enabled: bool | None = None
    max_cycles_per_session: int | None = Field(None, ge=1, le=100)
    alert_tier_threshold: int | None = Field(None, ge=1, le=4)
    cycle_interval_seconds: int | None = Field(None, ge=60, le=3600)
