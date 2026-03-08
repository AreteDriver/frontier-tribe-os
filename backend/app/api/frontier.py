"""EVE Frontier World API client wrapper.

Wraps all external API calls with error handling and static data fallback.
Document failures in docs/API_NOTES.md.
"""

import json
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://blockchain-gateway-nova.nursery.reitnorf.com/v1"
STATIC_DATA_DIR = Path(__file__).parent.parent.parent / "data"


async def get_character(character_id: str) -> dict | None:
    """Fetch character info from World API."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/characters/{character_id}")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning("World API character fetch failed: %s", e)
        return None


async def get_item_types() -> list[dict]:
    """Fetch item/blueprint types. Falls back to static JSON."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/types")
            resp.raise_for_status()
            return resp.json()
    except Exception:
        logger.warning("World API types fetch failed, using static fallback")
        return _load_static("blueprints.json")


async def get_blueprint_materials(type_id: str) -> dict | None:
    """Fetch material requirements for a blueprint."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/types/{type_id}")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning("World API blueprint materials fetch failed: %s", e)
        return _load_static_blueprint(type_id)


def _load_static(filename: str) -> list[dict]:
    path = STATIC_DATA_DIR / filename
    if path.exists():
        return json.loads(path.read_text())
    return []


def _load_static_blueprint(type_id: str) -> dict | None:
    blueprints = _load_static("blueprints.json")
    for bp in blueprints:
        if str(bp.get("type_id")) == str(type_id):
            return bp
    return None
