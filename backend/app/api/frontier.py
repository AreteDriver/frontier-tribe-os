"""EVE Frontier World API client wrapper.

Wraps all external API calls with error handling and static data fallback.
Document failures in docs/API_NOTES.md.
"""

import json
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://blockchain-gateway-stillness.live.tech.evefrontier.com"
STATIC_DATA_DIR = Path(__file__).parent.parent.parent / "data"


async def get_character(character_id: str) -> dict | None:
    """Fetch character info from World API."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/v2/smartcharacters/{character_id}")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning("World API character fetch failed: %s", e)
        return None


async def get_item_types() -> list[dict]:
    """Fetch item/blueprint types. Falls back to static JSON."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/v2/types")
            resp.raise_for_status()
            return resp.json()
    except Exception:
        logger.warning("World API types fetch failed, using static fallback")
        return _load_static("blueprints.json")


async def get_blueprint_materials(type_id: str) -> dict | None:
    """Fetch material requirements for a blueprint."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/v2/types/{type_id}")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning("World API blueprint materials fetch failed: %s", e)
        return _load_static_blueprint(type_id)


async def get_tribes() -> list[dict]:
    """Fetch all tribes from World API."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/v2/tribes", params={"limit": 1000})
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning("World API tribes fetch failed: %s", e)
        return []


async def get_tribe(tribe_id: str) -> dict | None:
    """Fetch a single tribe from World API."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/v2/tribes/{tribe_id}")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning("World API tribe fetch failed: %s", e)
        return None


async def get_smart_assemblies(assembly_type: str | None = None) -> list[dict]:
    """Fetch smart assemblies, optionally filtered by type."""
    try:
        params: dict = {"limit": 100}
        if assembly_type:
            params["type"] = assembly_type
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/v2/smartassemblies", params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning("World API assemblies fetch failed: %s", e)
        return []


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
