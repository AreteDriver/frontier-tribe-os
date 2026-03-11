"""Tests for the Discord notifier."""

import pytest

from app.notifications.notifier import DiscordNotifier


@pytest.mark.asyncio
async def test_dry_run_sends_nothing():
    """Dry run mode logs but doesn't send."""
    notifier = DiscordNotifier(webhook_url="", dry_run=True)
    result = await notifier.send_alert("feral_ai_evolved", zone="Alpha", tier=2)
    assert result is True


@pytest.mark.asyncio
async def test_no_webhook_url():
    """No webhook URL returns False without error."""
    notifier = DiscordNotifier(webhook_url="", dry_run=False)
    result = await notifier.send_alert("feral_ai_evolved", zone="Alpha", tier=2)
    assert result is False


@pytest.mark.asyncio
async def test_unknown_alert_type():
    """Unknown alert type returns False."""
    notifier = DiscordNotifier(webhook_url="", dry_run=True)
    result = await notifier.send_alert("nonexistent_type")
    assert result is False


@pytest.mark.asyncio
async def test_feral_ai_evolved_convenience():
    """Convenience method routes to correct alert type."""
    notifier = DiscordNotifier(webhook_url="", dry_run=True)
    result = await notifier.feral_ai_evolved(zone="Beta", tier=1)
    assert result is True


@pytest.mark.asyncio
async def test_feral_ai_critical_routing():
    """Tier >= 3 routes to ai_critical alert."""
    notifier = DiscordNotifier(webhook_url="", dry_run=True)
    result = await notifier.feral_ai_evolved(zone="Gamma", tier=3)
    assert result is True


@pytest.mark.asyncio
async def test_hostile_scan():
    """Hostile scan alert works in dry run."""
    notifier = DiscordNotifier(webhook_url="", dry_run=True)
    result = await notifier.hostile_scan(zone="Delta", scanner="TestPilot")
    assert result is True


@pytest.mark.asyncio
async def test_blind_spot():
    """Blind spot alert works in dry run."""
    notifier = DiscordNotifier(webhook_url="", dry_run=True)
    result = await notifier.blind_spot(zone="Epsilon", minutes=25)
    assert result is True


@pytest.mark.asyncio
async def test_clone_reserve_low():
    """Clone reserve low alert works in dry run."""
    notifier = DiscordNotifier(webhook_url="", dry_run=True)
    result = await notifier.clone_reserve_low(count=3)
    assert result is True
