"""Background poller for EVE Frontier World API data sync.

Periodically fetches tribes, killmails, and smart assemblies from the
World API and upserts local records / logs relevant events.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Killmail, Tribe
from app.db.session import async_session

logger = logging.getLogger(__name__)

WORLD_API_BASE = "https://blockchain-gateway-stillness.live.tech.evefrontier.com"


class WorldAPIPoller:
    """Periodically syncs data from the EVE Frontier World API."""

    def __init__(self, interval_seconds: int = 300):
        self.interval_seconds = interval_seconds
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the background polling loop."""
        if self._running:
            logger.warning("Poller already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("World API poller started (interval=%ds)", self.interval_seconds)

    async def stop(self):
        """Stop the background polling loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("World API poller stopped")

    async def poll_once(self):
        """Run a single poll cycle. Useful for testing."""
        async with httpx.AsyncClient(base_url=WORLD_API_BASE, timeout=15) as client:
            await self._sync_tribes(client)
            await self._sync_killmails(client)
            await self._sync_assemblies(client)

    # -- internal --

    async def _loop(self):
        """Main polling loop — runs until stopped."""
        while self._running:
            try:
                await self.poll_once()
            except Exception:
                logger.exception("Unhandled error in poll cycle")
            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break

    async def _sync_tribes(self, client: httpx.AsyncClient):
        """Fetch tribes from World API and upsert into local DB."""
        try:
            resp = await client.get("/v2/tribes", params={"limit": 1000})
            resp.raise_for_status()
            data = resp.json()
            tribes = data.get("data", data) if isinstance(data, dict) else data

            async with async_session() as db:
                upserted = 0
                for t in tribes:
                    world_id = t.get("id")
                    if world_id is None:
                        continue
                    upserted += await self._upsert_tribe(db, t, world_id)
                await db.commit()
                logger.info("sync_tribes: upserted %d/%d tribes", upserted, len(tribes))
        except httpx.HTTPError as e:
            logger.warning("sync_tribes failed: %s", e)
        except Exception:
            logger.exception("sync_tribes unexpected error")

    async def _upsert_tribe(self, db: AsyncSession, data: dict, world_id: int) -> int:
        """Upsert a single tribe row. Returns 1 if written, 0 if skipped."""
        result = await db.execute(select(Tribe).where(Tribe.world_tribe_id == world_id))
        tribe = result.scalar_one_or_none()

        name = data.get("name", f"Tribe-{world_id}")
        if tribe:
            tribe.name = name
            tribe.name_short = data.get("nameShort") or tribe.name_short
            tribe.leader_address = data.get("leaderAddress") or tribe.leader_address
            tribe.token_contract_address = (
                data.get("tokenContractAddress") or tribe.token_contract_address
            )
        else:
            tribe = Tribe(
                world_tribe_id=world_id,
                name=name,
                name_short=data.get("nameShort"),
                leader_address=data.get("leaderAddress"),
                token_contract_address=data.get("tokenContractAddress"),
            )
            db.add(tribe)
        return 1

    async def _sync_killmails(self, client: httpx.AsyncClient):
        """Fetch recent killmails and persist to DB. Upsert by kill_id."""
        try:
            resp = await client.get("/v2/killmails", params={"limit": 50})
            resp.raise_for_status()
            data = resp.json()
            killmails = data.get("data", data) if isinstance(data, dict) else data

            async with async_session() as db:
                inserted = 0
                for km in killmails:
                    km_id = km.get("id")
                    if km_id is None:
                        continue
                    inserted += await self._upsert_killmail(db, km, km_id)
                await db.commit()
                logger.info(
                    "sync_killmails: inserted %d/%d killmails",
                    inserted,
                    len(killmails),
                )
        except httpx.HTTPError as e:
            logger.warning("sync_killmails failed: %s", e)
        except Exception:
            logger.exception("sync_killmails unexpected error")

    async def _upsert_killmail(self, db: AsyncSession, data: dict, km_id: int) -> int:
        """Upsert a single killmail. Returns 1 if inserted, 0 if skipped."""
        result = await db.execute(select(Killmail).where(Killmail.kill_id == km_id))
        if result.scalar_one_or_none() is not None:
            return 0  # Already exists

        killer_obj = data.get("killer", {})
        victim_obj = data.get("victim", {})

        # Parse timestamp
        time_str = data.get("time", "")
        try:
            ts = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            ts = datetime.now(timezone.utc)

        killmail = Killmail(
            kill_id=km_id,
            victim_address=victim_obj.get("address", "0x0"),
            victim_name=victim_obj.get("name"),
            killer_address=killer_obj.get("address", "0x0"),
            killer_name=killer_obj.get("name"),
            solar_system_id=data.get("solarSystemId"),
            timestamp=ts,
            raw_json=json.dumps(data),
        )
        db.add(killmail)
        return 1

    async def _sync_assemblies(self, client: httpx.AsyncClient):
        """Fetch smart assemblies and log counts by type."""
        try:
            resp = await client.get("/v2/smartassemblies", params={"limit": 50})
            resp.raise_for_status()
            data = resp.json()
            assemblies = data.get("data", data) if isinstance(data, dict) else data

            counts: dict[str, int] = {}
            for a in assemblies:
                a_type = a.get("type", "Unknown")
                counts[a_type] = counts.get(a_type, 0) + 1

            logger.info("sync_assemblies: %s", counts)
        except httpx.HTTPError as e:
            logger.warning("sync_assemblies failed: %s", e)
        except Exception:
            logger.exception("sync_assemblies unexpected error")
