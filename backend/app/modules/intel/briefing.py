"""LLM-powered intel briefing service using Anthropic API via httpx."""

import json
import logging
import time
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"

SYSTEM_PROMPT = (
    "You are an EVE Frontier intelligence officer. You receive raw operational data "
    "and produce concise, actionable fleet commander briefs. Be direct. Use military "
    "brevity. Flag threats, opportunities, and recommended actions."
)

USER_PROMPT_TEMPLATE = """Zone: {zone_name}
Time window: last {hours_back} hours

Kill activity: {kill_count} kills
Active hostiles: {hostile_summary}
Scan results: {scan_summary}
Threat indicators: {threat_summary}
Last engagement: {last_engagement}

Produce an intel brief covering:
1. Threat level (Low/Medium/High/Critical)
2. Active hostile organizations
3. Last known fleet composition and time
4. Recommended action (avoid / scout / engage / fortify)
5. Key intelligence gaps

Keep it under 150 words."""

# Cache: key -> (result_dict, timestamp)
_briefing_cache: dict[str, tuple[dict, float]] = {}
CACHE_TTL_SECONDS = 15 * 60  # 15 minutes


def _cache_key(zone_id: str, hours_back: int) -> str:
    return f"{zone_id}:{hours_back}"


def get_cached_brief(zone_id: str, hours_back: int) -> dict | None:
    """Return cached brief if still valid, else None."""
    key = _cache_key(zone_id, hours_back)
    entry = _briefing_cache.get(key)
    if entry is None:
        return None
    result, ts = entry
    if time.time() - ts > CACHE_TTL_SECONDS:
        del _briefing_cache[key]
        return None
    return result


def set_cached_brief(zone_id: str, hours_back: int, result: dict) -> None:
    key = _cache_key(zone_id, hours_back)
    _briefing_cache[key] = (result, time.time())


def clear_cache() -> None:
    """Clear all cached briefs (useful for testing)."""
    _briefing_cache.clear()


class IntelBriefingService:
    """Generates AI-powered operational briefs for fleet commanders."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def generate_brief(
        self,
        zone_name: str,
        zone_id: str,
        hours_back: int,
        kills: list,
        scans: list,
        threats: list,
    ) -> dict:
        """Format context and call Anthropic API. Returns brief dict.

        If no API key is configured, returns a mock brief.
        """
        # Check cache first
        cached = get_cached_brief(zone_id, hours_back)
        if cached is not None:
            return cached

        now = datetime.now(timezone.utc)

        if not self.api_key:
            result = {
                "summary": "Intel briefing unavailable — no API key configured",
                "threat_level": "UNKNOWN",
                "recommended_action": "Configure ANTHROPIC_API_KEY for LLM intel",
                "generated_at": now.isoformat(),
            }
            set_cached_brief(zone_id, hours_back, result)
            return result

        # Build context from raw data
        kill_count = len(kills)
        hostile_summary = self._summarize_hostiles(kills)
        scan_summary = self._summarize_scans(scans)
        threat_summary = self._summarize_threats(threats)
        last_engagement = self._last_engagement(kills)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            zone_name=zone_name,
            hours_back=hours_back,
            kill_count=kill_count,
            hostile_summary=hostile_summary,
            scan_summary=scan_summary,
            threat_summary=threat_summary,
            last_engagement=last_engagement,
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    ANTHROPIC_API_URL,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": ANTHROPIC_VERSION,
                        "content-type": "application/json",
                    },
                    json={
                        "model": ANTHROPIC_MODEL,
                        "max_tokens": 300,
                        "system": SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": user_prompt}],
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            # Extract text from Anthropic response
            content_blocks = data.get("content", [])
            text = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    text += block.get("text", "")

            # Parse threat level from response text
            threat_level = self._extract_threat_level(text)

            result = {
                "summary": text.strip(),
                "threat_level": threat_level,
                "recommended_action": self._extract_recommended_action(text),
                "generated_at": now.isoformat(),
            }
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Anthropic API error: %s %s",
                exc.response.status_code,
                exc.response.text,
            )
            result = {
                "summary": f"Intel briefing failed — API error {exc.response.status_code}",
                "threat_level": "UNKNOWN",
                "recommended_action": "Retry later or check API key",
                "generated_at": now.isoformat(),
            }
        except (httpx.RequestError, json.JSONDecodeError) as exc:
            logger.error("Anthropic API request failed: %s", exc)
            result = {
                "summary": "Intel briefing failed — connection error",
                "threat_level": "UNKNOWN",
                "recommended_action": "Check network connectivity",
                "generated_at": now.isoformat(),
            }

        set_cached_brief(zone_id, hours_back, result)
        return result

    def _summarize_hostiles(self, kills: list) -> str:
        if not kills:
            return "No hostile activity detected"
        # Collect unique attacker info
        attackers: set[str] = set()
        for k in kills:
            name = getattr(k, "killer_name", None) or "Unknown"
            attackers.add(name)
        if len(attackers) > 5:
            sample = list(attackers)[:5]
            return f"{len(attackers)} hostiles detected: {', '.join(sample)} and others"
        return f"{len(attackers)} hostiles: {', '.join(attackers)}"

    def _summarize_scans(self, scans: list) -> str:
        if not scans:
            return "No recent scans"
        by_type: dict[str, int] = {}
        for s in scans:
            rt = getattr(s, "result_type", "UNKNOWN")
            by_type[rt] = by_type.get(rt, 0) + 1
        parts = [f"{count} {rtype}" for rtype, count in by_type.items()]
        return f"{len(scans)} scans: {', '.join(parts)}"

    def _summarize_threats(self, threats: list) -> str:
        if not threats:
            return "No active threat indicators"
        severities = [getattr(t, "severity", 1) for t in threats]
        max_sev = max(severities)
        return f"{len(threats)} threat events (max severity: {max_sev}/5)"

    def _last_engagement(self, kills: list) -> str:
        if not kills:
            return "No recent engagements"
        # Assume kills are sorted desc by timestamp
        latest = kills[0]
        ts = getattr(latest, "timestamp", None)
        if ts:
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts.isoformat()
        return "Unknown time"

    def _extract_threat_level(self, text: str) -> str:
        text_upper = text.upper()
        for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            if level in text_upper:
                return level
        return "UNKNOWN"

    def _extract_recommended_action(self, text: str) -> str:
        text_lower = text.lower()
        for action in ("fortify", "avoid", "engage", "scout"):
            if action in text_lower:
                return action.capitalize()
        return "Monitor"
