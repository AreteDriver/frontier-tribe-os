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


# --- Pilot Intelligence ---


class ActiveHour(BaseModel):
    hour: int
    count: int


class PilotProfileResponse(BaseModel):
    """Pilot intelligence profile computed from killmail data."""

    address: str
    name: str | None = None
    kill_count: int
    death_count: int
    kd_ratio: float
    primary_systems: list[TopSystem]
    active_hours: list[ActiveHour]
    recent_kills: list[KillmailResponse]
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    threat_level: str


class PilotSearchResult(BaseModel):
    address: str
    name: str | None = None
    kill_count: int = 0
    death_count: int = 0


# --- Corp Intelligence ---


class TopKiller(BaseModel):
    address: str
    name: str | None = None
    kill_count: int


class CorpProfileResponse(BaseModel):
    """Corp intelligence profile computed from killmail data."""

    corp_id: int
    corp_name: str | None = None
    kill_count: int
    death_count: int
    efficiency: float
    member_addresses: list[str]
    primary_systems: list[TopSystem]
    recent_kills: list[KillmailResponse]
    top_killers: list[TopKiller]


class CorpLeaderboardEntry(BaseModel):
    corp_id: int
    corp_name: str | None = None
    kill_count: int
