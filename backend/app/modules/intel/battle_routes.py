"""Battle detection and report endpoints."""

import hashlib
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import get_current_member
from app.config import settings
from app.db.models import Killmail, Member
from app.db.session import get_db

from .schemas import (
    BattleDetailResponse,
    BattleSide,
    BattleSummary,
    BattleTimelineEntry,
)

logger = logging.getLogger(__name__)

router = APIRouter()

BATTLE_WINDOW_MINUTES = 30
MIN_KILLS_FOR_BATTLE = 3


def _compute_battle_id(solar_system_id: int, start_time: datetime) -> str:
    """Deterministic battle ID from system + window start."""
    raw = f"{solar_system_id}:{start_time.isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _cluster_killmails(killmails: list[Killmail]) -> list[list[Killmail]]:
    """Cluster killmails within BATTLE_WINDOW_MINUTES of each other."""
    if not killmails:
        return []
    sorted_kms = sorted(killmails, key=lambda k: k.timestamp)
    clusters: list[list[Killmail]] = [[sorted_kms[0]]]
    for km in sorted_kms[1:]:
        last_ts = clusters[-1][-1].timestamp
        if (km.timestamp - last_ts).total_seconds() <= BATTLE_WINDOW_MINUTES * 60:
            clusters[-1].append(km)
        else:
            clusters.append([km])
    return clusters


def _build_sides(killmails: list[Killmail]) -> list[BattleSide]:
    """Group participants into sides by corp_id."""
    corp_data: dict[int | None, dict] = {}
    for km in killmails:
        k_corp = km.killer_corp_id
        if k_corp not in corp_data:
            corp_data[k_corp] = {
                "corp_name": km.killer_corp_name,
                "corp_id": k_corp,
                "kills": 0,
                "deaths": 0,
                "addresses": set(),
            }
        corp_data[k_corp]["kills"] += 1
        corp_data[k_corp]["addresses"].add(km.killer_address)
        if km.killer_corp_name and not corp_data[k_corp]["corp_name"]:
            corp_data[k_corp]["corp_name"] = km.killer_corp_name

        v_corp = km.victim_corp_id
        if v_corp not in corp_data:
            corp_data[v_corp] = {
                "corp_name": km.victim_corp_name,
                "corp_id": v_corp,
                "kills": 0,
                "deaths": 0,
                "addresses": set(),
            }
        corp_data[v_corp]["deaths"] += 1
        corp_data[v_corp]["addresses"].add(km.victim_address)
        if km.victim_corp_name and not corp_data[v_corp]["corp_name"]:
            corp_data[v_corp]["corp_name"] = km.victim_corp_name

    sides = []
    for data in corp_data.values():
        total = data["kills"] + data["deaths"]
        efficiency = round((data["kills"] / total) * 100, 1) if total > 0 else 0.0
        sides.append(
            BattleSide(
                corp_name=data["corp_name"],
                corp_id=data["corp_id"],
                kill_count=data["kills"],
                death_count=data["deaths"],
                addresses=sorted(data["addresses"]),
                efficiency=efficiency,
            )
        )
    sides.sort(key=lambda s: s.kill_count, reverse=True)
    return sides


def _build_preview(killmails: list[Killmail], max_items: int = 3) -> list[str]:
    """First N kill descriptions for preview."""
    previews = []
    sorted_kms = sorted(killmails, key=lambda k: k.timestamp)
    for km in sorted_kms[:max_items]:
        killer = km.killer_name or km.killer_address[:10]
        victim = km.victim_name or km.victim_address[:10]
        previews.append(f"{killer} killed {victim}")
    return previews


async def _detect_battles(db: AsyncSession) -> list[dict]:
    """Detect battles from all killmails, return sorted by total_kills desc."""
    result = await db.execute(
        select(Killmail)
        .where(Killmail.solar_system_id.is_not(None))
        .order_by(Killmail.solar_system_id, Killmail.timestamp)
    )
    all_kms = list(result.scalars().all())

    by_system: dict[int, list[Killmail]] = {}
    for km in all_kms:
        sid = km.solar_system_id
        if sid is not None:
            by_system.setdefault(sid, []).append(km)

    battles = []
    for system_id, kms in by_system.items():
        clusters = _cluster_killmails(kms)
        for cluster in clusters:
            if len(cluster) < MIN_KILLS_FOR_BATTLE:
                continue
            start_time = min(k.timestamp for k in cluster)
            end_time = max(k.timestamp for k in cluster)
            battle_id = _compute_battle_id(system_id, start_time)
            sides = _build_sides(cluster)
            preview = _build_preview(cluster)
            battles.append(
                {
                    "battle_id": battle_id,
                    "solar_system_id": system_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "total_kills": len(cluster),
                    "sides": sides,
                    "preview": preview,
                    "killmails": cluster,
                }
            )

    battles.sort(key=lambda b: b["total_kills"], reverse=True)
    return battles


@router.get("/battles", response_model=list[BattleSummary])
async def list_battles(
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """List detected battles (clusters of 3+ kills in same system within 30min)."""
    battles = await _detect_battles(db)
    return [
        BattleSummary(
            battle_id=b["battle_id"],
            solar_system_id=b["solar_system_id"],
            start_time=b["start_time"],
            end_time=b["end_time"],
            total_kills=b["total_kills"],
            sides=b["sides"],
            preview=b["preview"],
        )
        for b in battles
    ]


@router.get("/battles/{battle_id}", response_model=BattleDetailResponse)
async def get_battle(
    battle_id: str,
    member: Member = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
):
    """Full battle report with timeline and optional LLM narrative."""
    battles = await _detect_battles(db)
    battle = next((b for b in battles if b["battle_id"] == battle_id), None)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")

    killmails = battle["killmails"]
    timeline = [
        BattleTimelineEntry(
            kill_id=km.kill_id,
            killer_name=km.killer_name,
            killer_address=km.killer_address,
            killer_corp_name=km.killer_corp_name,
            victim_name=km.victim_name,
            victim_address=km.victim_address,
            victim_corp_name=km.victim_corp_name,
            timestamp=km.timestamp,
        )
        for km in sorted(killmails, key=lambda k: k.timestamp)
    ]

    duration = (battle["end_time"] - battle["start_time"]).total_seconds() / 60.0
    duration_minutes = round(duration, 1)

    narrative = None
    if settings.anthropic_api_key:
        try:
            sides_text = ", ".join(
                f"{s.corp_name or 'Unknown'} ({s.kill_count}K/{s.death_count}D)"
                for s in battle["sides"]
            )
            prompt_data = {
                "zone_name": f"System {battle['solar_system_id']}",
                "hours_back": max(1, int(duration_minutes / 60) + 1),
                "kill_count": battle["total_kills"],
                "hostile_summary": sides_text,
                "scan_summary": f"Battle: {battle['total_kills']} kills over {duration_minutes}min",
                "threat_summary": f"Sides: {sides_text}",
                "last_engagement": battle["end_time"].isoformat(),
            }
            from .briefing import (
                ANTHROPIC_API_URL,
                ANTHROPIC_MODEL,
                ANTHROPIC_VERSION,
                SYSTEM_PROMPT,
                USER_PROMPT_TEMPLATE,
            )

            user_prompt = USER_PROMPT_TEMPLATE.format(**prompt_data)

            async with httpx.AsyncClient(timeout=30.0) as http_client:
                resp = await http_client.post(
                    ANTHROPIC_API_URL,
                    headers={
                        "x-api-key": settings.anthropic_api_key,
                        "anthropic-version": ANTHROPIC_VERSION,
                        "content-type": "application/json",
                    },
                    json={
                        "model": ANTHROPIC_MODEL,
                        "max_tokens": 300,
                        "system": SYSTEM_PROMPT
                        + " Generate a battle after-action report.",
                        "messages": [{"role": "user", "content": user_prompt}],
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        narrative = block.get("text", "").strip()
                        break
        except (httpx.HTTPError, KeyError, ValueError):
            logger.exception("Failed to generate battle narrative")
            narrative = None

    return BattleDetailResponse(
        battle_id=battle["battle_id"],
        solar_system_id=battle["solar_system_id"],
        start_time=battle["start_time"],
        end_time=battle["end_time"],
        total_kills=battle["total_kills"],
        duration_minutes=duration_minutes,
        sides=battle["sides"],
        timeline=timeline,
        narrative=narrative,
    )
