"""Schemas for the Intel module — killmail feed and stats."""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, computed_field


class KillmailResponse(BaseModel):
    """Single killmail response."""

    id: uuid.UUID
    kill_id: int
    victim_address: str
    victim_name: str | None = None
    victim_corp_id: int | None = None
    victim_corp_name: str | None = None
    killer_address: str
    killer_name: str | None = None
    killer_corp_id: int | None = None
    killer_corp_name: str | None = None
    solar_system_id: int | None = None
    timestamp: datetime
    cycle: int
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def time_ago(self) -> str:
        """Human-readable time since kill."""
        now = datetime.now(timezone.utc)
        ts = (
            self.timestamp.replace(tzinfo=timezone.utc)
            if self.timestamp.tzinfo is None
            else self.timestamp
        )
        delta = now - ts
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        return f"{days}d ago"

    model_config = {"from_attributes": True}


class KillmailDetailResponse(KillmailResponse):
    """Single killmail with raw JSON detail."""

    raw_json: str | None = None


class HourlyKills(BaseModel):
    hour: str
    count: int


class TopSystem(BaseModel):
    solar_system_id: int
    count: int


class KillmailStatsResponse(BaseModel):
    """Aggregated killmail statistics."""

    hourly_kills: list[HourlyKills]
    top_systems: list[TopSystem]
    total_24h: int
    total_7d: int
