"""Alert configuration endpoints — self-service Discord alerts for tribes."""

import logging
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_member
from app.db.models import AlertConfig, Member
from app.db.session import get_db

from .schemas import AlertConfigCreate, AlertConfigResponse, AlertConfigUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertConfigResponse])
async def list_alerts(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """List all alert configs for the current member's tribe."""
    if not member.tribe_id:
        raise HTTPException(status_code=400, detail="Not in a tribe")

    result = await db.execute(
        select(AlertConfig)
        .where(AlertConfig.tribe_id == member.tribe_id)
        .order_by(AlertConfig.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=AlertConfigResponse, status_code=201)
async def create_alert(
    body: AlertConfigCreate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert config. Requires tribe membership."""
    if not member.tribe_id:
        raise HTTPException(status_code=400, detail="Not in a tribe")

    alert = AlertConfig(
        tribe_id=member.tribe_id,
        created_by=member.id,
        alert_type=body.alert_type,
        target_id=body.target_id,
        target_name=body.target_name,
        threshold=body.threshold,
        discord_webhook_url=body.discord_webhook_url,
        cooldown_minutes=body.cooldown_minutes,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.patch("/{alert_id}", response_model=AlertConfigResponse)
async def update_alert(
    alert_id: UUID,
    body: AlertConfigUpdate,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Update alert config (enable/disable, threshold, cooldown)."""
    if not member.tribe_id:
        raise HTTPException(status_code=400, detail="Not in a tribe")

    alert = await db.get(AlertConfig, alert_id)
    if not alert or alert.tribe_id != member.tribe_id:
        raise HTTPException(status_code=404, detail="Alert not found")

    if body.enabled is not None:
        alert.enabled = body.enabled
    if body.threshold is not None:
        alert.threshold = body.threshold
    if body.cooldown_minutes is not None:
        alert.cooldown_minutes = body.cooldown_minutes

    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert config. Must belong to same tribe."""
    if not member.tribe_id:
        raise HTTPException(status_code=400, detail="Not in a tribe")

    alert = await db.get(AlertConfig, alert_id)
    if not alert or alert.tribe_id != member.tribe_id:
        raise HTTPException(status_code=404, detail="Alert not found")

    await db.delete(alert)
    await db.commit()


@router.post("/{alert_id}/test")
async def test_alert(
    alert_id: UUID,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Send a test alert through the configured webhook."""
    if not member.tribe_id:
        raise HTTPException(status_code=400, detail="Not in a tribe")

    alert = await db.get(AlertConfig, alert_id)
    if not alert or alert.tribe_id != member.tribe_id:
        raise HTTPException(status_code=404, detail="Alert not found")

    payload = {
        "embeds": [
            {
                "title": "TEST ALERT",
                "description": (
                    f"Alert type: {alert.alert_type}\n"
                    f"Target: {alert.target_name or alert.target_id or 'N/A'}\n"
                    f"Threshold: {alert.threshold}\n"
                    f"Cooldown: {alert.cooldown_minutes}m"
                ),
                "color": 0x00FF00,  # Green for test
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {"text": "Frontier Tribe OS // Alert Test"},
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(alert.discord_webhook_url, json=payload)
            if resp.status_code in (200, 204):
                return {"sent": True, "status_code": resp.status_code}
            return {"sent": False, "status_code": resp.status_code}
    except Exception:
        logger.exception("Failed to send test alert for %s", alert_id)
        return {"sent": False, "error": "Failed to reach Discord webhook"}
