"""Discord webhook notifier for C5 Watch alerts.

Alert types:
  - feral_ai_evolved: Feral AI tier increase
  - hostile_scan: Hostile void scan result
  - blind_spot: Zone not scanned in >20 min
  - clone_reserve_low: Active clones below threshold
  - ai_critical: Feral AI reached CRITICAL tier

Usage:
  notifier = DiscordNotifier(webhook_url)
  await notifier.send_alert("feral_ai_evolved", zone="Alpha Sector", tier=3)

  # Dry-run mode (logs instead of sending):
  notifier = DiscordNotifier(webhook_url, dry_run=True)
"""

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

ALERT_TEMPLATES = {
    "feral_ai_evolved": {
        "emoji": "\u26a0\ufe0f",
        "title": "FERAL AI EVOLVED",
        "template": "{zone} reached Tier {tier}",
        "color": 0xFFA500,  # Orange
    },
    "hostile_scan": {
        "emoji": "\U0001f534",
        "title": "HOSTILE DETECTED",
        "template": "{zone} scan by {scanner}",
        "color": 0xFF0000,  # Red
    },
    "blind_spot": {
        "emoji": "\U0001f441\ufe0f",
        "title": "BLIND SPOT",
        "template": "{zone} unseen for {minutes}m",
        "color": 0xFFFF00,  # Yellow
    },
    "clone_reserve_low": {
        "emoji": "\u26a0\ufe0f",
        "title": "CLONE RESERVE LOW",
        "template": "{count} active clones remaining",
        "color": 0xFFA500,  # Orange
    },
    "ai_critical": {
        "emoji": "\U0001f6a8",
        "title": "CRITICAL FERAL AI",
        "template": "{zone} requires immediate response",
        "color": 0x800080,  # Purple
    },
}


class DiscordNotifier:
    """Send structured alerts to a Discord webhook."""

    def __init__(self, webhook_url: str, dry_run: bool = False):
        self.webhook_url = webhook_url
        self.dry_run = dry_run

    async def send_alert(self, alert_type: str, **kwargs: str | int) -> bool:
        """Send a typed alert. Returns True if sent successfully."""
        template = ALERT_TEMPLATES.get(alert_type)
        if not template:
            logger.error("Unknown alert type: %s", alert_type)
            return False

        message = template["template"].format(**kwargs)
        title = f"{template['emoji']} {template['title']}"
        full_message = f"{title} \u2014 {message}"

        if self.dry_run:
            logger.info("[DRY RUN] Discord alert: %s", full_message)
            return True

        if not self.webhook_url:
            logger.warning("Discord webhook URL not configured, skipping alert")
            return False

        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": message,
                    "color": template["color"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "footer": {"text": "Frontier Tribe OS // Watch Module"},
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.webhook_url, json=payload)
                if resp.status_code in (200, 204):
                    logger.info("Discord alert sent: %s", alert_type)
                    return True
                logger.warning(
                    "Discord webhook returned %d: %s",
                    resp.status_code,
                    resp.text[:200],
                )
                return False
        except Exception:
            logger.exception("Failed to send Discord alert: %s", alert_type)
            return False

    async def feral_ai_evolved(self, zone: str, tier: int) -> bool:
        """Alert: feral AI tier increased."""
        alert = "ai_critical" if tier >= 3 else "feral_ai_evolved"
        return await self.send_alert(alert, zone=zone, tier=tier)

    async def hostile_scan(self, zone: str, scanner: str) -> bool:
        """Alert: hostile void scan result."""
        return await self.send_alert("hostile_scan", zone=zone, scanner=scanner)

    async def blind_spot(self, zone: str, minutes: int) -> bool:
        """Alert: zone unseen for too long."""
        return await self.send_alert("blind_spot", zone=zone, minutes=minutes)

    async def clone_reserve_low(self, count: int) -> bool:
        """Alert: active clones below threshold."""
        return await self.send_alert("clone_reserve_low", count=count)
