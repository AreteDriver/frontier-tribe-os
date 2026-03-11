"""Tests for LLM Intel Briefing — service and endpoints."""

import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.modules.intel.briefing import (
    IntelBriefingService,
    clear_cache,
    get_cached_brief,
    set_cached_brief,
)


@pytest.fixture(autouse=True)
def _clear_briefing_cache():
    """Ensure cache is clean before and after each test."""
    clear_cache()
    yield
    clear_cache()


# --- Service tests ---


@pytest.mark.asyncio
async def test_generate_brief_no_api_key():
    """With no API key, returns mock brief with UNKNOWN threat level."""
    service = IntelBriefingService(api_key="")
    result = await service.generate_brief(
        zone_name="Alpha Sector",
        zone_id="zone-123",
        hours_back=4,
        kills=[],
        scans=[],
        threats=[],
    )
    assert result["threat_level"] == "UNKNOWN"
    assert "no API key" in result["summary"]
    assert "generated_at" in result


@pytest.mark.asyncio
async def test_generate_brief_with_mock_api():
    """Patch httpx to verify prompt construction and response parsing."""
    mock_response = httpx.Response(
        200,
        json={
            "content": [
                {
                    "type": "text",
                    "text": (
                        "THREAT LEVEL: HIGH\n\n"
                        "Active hostiles detected in Alpha Sector. "
                        "Recommend avoid until further intel gathered. "
                        "Key gap: no scan data in last 2 hours."
                    ),
                }
            ],
            "model": "claude-haiku-4-5-20251001",
            "usage": {"input_tokens": 100, "output_tokens": 50},
        },
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
    )

    with patch("app.modules.intel.briefing.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        service = IntelBriefingService(api_key="test-key-123")
        result = await service.generate_brief(
            zone_name="Alpha Sector",
            zone_id="zone-456",
            hours_back=4,
            kills=[],
            scans=[],
            threats=[],
        )

        assert result["threat_level"] == "HIGH"
        assert "Alpha Sector" in result["summary"]
        assert result["recommended_action"] == "Avoid"
        assert "generated_at" in result

        # Verify API was called with correct headers
        call_kwargs = mock_client.post.call_args
        assert call_kwargs[0][0] == "https://api.anthropic.com/v1/messages"
        headers = call_kwargs[1]["headers"]
        assert headers["x-api-key"] == "test-key-123"
        assert headers["anthropic-version"] == "2023-06-01"


@pytest.mark.asyncio
async def test_briefing_cache():
    """Second call within 15 min returns cached result without API call."""
    service = IntelBriefingService(api_key="")

    # First call — generates mock
    result1 = await service.generate_brief(
        zone_name="Alpha",
        zone_id="zone-cache-test",
        hours_back=4,
        kills=[],
        scans=[],
        threats=[],
    )

    # Second call — should return cached
    result2 = await service.generate_brief(
        zone_name="Alpha",
        zone_id="zone-cache-test",
        hours_back=4,
        kills=[],
        scans=[],
        threats=[],
    )

    assert result1 == result2
    assert result1["threat_level"] == "UNKNOWN"

    # Verify it was cached
    cached = get_cached_brief("zone-cache-test", 4)
    assert cached is not None
    assert cached["threat_level"] == "UNKNOWN"


def test_cache_expiry():
    """Cached entries expire after TTL."""
    set_cached_brief("zone-exp", 4, {"summary": "test", "threat_level": "LOW"})

    # Should be cached
    assert get_cached_brief("zone-exp", 4) is not None

    # Manipulate cache timestamp to simulate expiry
    from app.modules.intel.briefing import _briefing_cache

    key = "zone-exp:4"
    result, _ = _briefing_cache[key]
    _briefing_cache[key] = (result, time.time() - 16 * 60)  # 16 min ago

    assert get_cached_brief("zone-exp", 4) is None


# --- Endpoint tests ---


@pytest.mark.asyncio
async def test_briefing_endpoint_no_zone(client, auth_headers):
    """POST /intel/briefing with non-existent zone returns 404."""
    resp = await client.post(
        "/intel/briefing",
        json={"zone_id": "00000000-0000-0000-0000-000000000000", "hours_back": 4},
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert "Zone not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_briefing_endpoint_success(client, auth_headers):
    """POST /intel/briefing with valid zone returns mock brief (no API key)."""
    # First create a zone
    zone_resp = await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-brief-test", "name": "Brief Test Sector"},
        headers=auth_headers,
    )
    assert zone_resp.status_code == 201
    zone_id = zone_resp.json()["id"]

    # Generate briefing
    resp = await client.post(
        "/intel/briefing",
        json={"zone_id": zone_id, "hours_back": 4},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["threat_level"] == "UNKNOWN"
    assert "no API key" in data["summary"]
    assert "generated_at" in data
    assert "recommended_action" in data


@pytest.mark.asyncio
async def test_briefing_zones_list(client, auth_headers):
    """GET /intel/briefing/zones returns zones with recent activity."""
    # Create a zone
    zone_resp = await client.post(
        "/watch/orbital-zones",
        json={"zone_id": "zone-list-test", "name": "List Test Sector"},
        headers=auth_headers,
    )
    assert zone_resp.status_code == 201
    zone_id = zone_resp.json()["id"]

    # Without any scans, zone should NOT appear
    resp = await client.get("/intel/briefing/zones", headers=auth_headers)
    assert resp.status_code == 200
    zone_ids = [z["zone_id"] for z in resp.json()]
    assert zone_id not in zone_ids

    # Submit a scan to the zone
    await client.post(
        "/watch/scans",
        json={
            "zone_id": zone_id,
            "result_type": "CLEAR",
            "resolution": 50,
            "confidence": 90,
        },
        headers=auth_headers,
    )

    # Now zone should appear in briefing zones
    resp = await client.get("/intel/briefing/zones", headers=auth_headers)
    assert resp.status_code == 200
    zone_ids = [z["zone_id"] for z in resp.json()]
    assert zone_id in zone_ids
