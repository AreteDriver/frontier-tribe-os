"""Schemas for alert configuration endpoints."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

VALID_ALERT_TYPES = {
    "kill_in_zone",
    "corp_spotted",
    "hostile_scan",
    "feral_evolved",
    "blind_spot",
    "clone_low",
}

DISCORD_WEBHOOK_PATTERN = re.compile(
    r"^https://(discord\.com|discordapp\.com)/api/webhooks/"
)


class AlertConfigCreate(BaseModel):
    alert_type: str
    target_id: str | None = None
    target_name: str | None = None
    threshold: int = 1
    discord_webhook_url: str
    cooldown_minutes: int = 5

    @field_validator("alert_type")
    @classmethod
    def validate_alert_type(cls, v: str) -> str:
        if v not in VALID_ALERT_TYPES:
            raise ValueError(
                f"Invalid alert_type. Must be one of: {sorted(VALID_ALERT_TYPES)}"
            )
        return v

    @field_validator("discord_webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str) -> str:
        if not DISCORD_WEBHOOK_PATTERN.match(v):
            raise ValueError(
                "Webhook URL must start with "
                "https://discord.com/api/webhooks/ or "
                "https://discordapp.com/api/webhooks/"
            )
        return v

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Threshold must be at least 1")
        return v

    @field_validator("cooldown_minutes")
    @classmethod
    def validate_cooldown(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Cooldown must be at least 1 minute")
        return v


class AlertConfigUpdate(BaseModel):
    enabled: bool | None = None
    threshold: int | None = None
    cooldown_minutes: int | None = None

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("Threshold must be at least 1")
        return v

    @field_validator("cooldown_minutes")
    @classmethod
    def validate_cooldown(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("Cooldown must be at least 1 minute")
        return v


class AlertConfigResponse(BaseModel):
    id: UUID
    tribe_id: UUID
    created_by: UUID
    alert_type: str
    target_id: str | None
    target_name: str | None
    threshold: int
    discord_webhook_url: str
    enabled: bool
    cooldown_minutes: int
    last_triggered: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
