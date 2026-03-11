"""Seed demo data for hackathon walkthrough.

Usage:
    cd backend && .venv/bin/python -m scripts.seed_demo

Importable:
    from scripts.seed_demo import seed
"""

import asyncio
import json
import logging
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure .env is loaded even when CWD is backend/ (the .env lives one level up)
_project_root = Path(__file__).resolve().parent.parent.parent
_env_file = _project_root / ".env"
if _env_file.exists() and not os.environ.get("DATABASE_URL"):
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

from sqlalchemy import select  # noqa: E402

from app.db.models import (  # noqa: E402
    CURRENT_CYCLE,
    AlertConfig,
    FeralAIEvent,
    Killmail,
    Member,
    OrbitalZone,
    ProductionJob,
    Scan,
    Tribe,
)
from app.db.session import async_session  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

NOW = datetime.now(timezone.utc)


def _ts_ago(**kwargs: int) -> datetime:
    """Return a UTC timestamp offset from now."""
    return NOW - timedelta(**kwargs)


def _rand_addr(prefix: str) -> str:
    """Generate a fake 0x address with a recognizable prefix."""
    return f"0x{prefix * 10}"[:42]


async def seed() -> None:
    """Populate the database with realistic demo data.

    Idempotent — skips if tribe 'Frontier Wolves' already exists.
    """
    async with async_session() as session:
        # --- Idempotency check ---
        result = await session.execute(
            select(Tribe).where(Tribe.name == "Frontier Wolves")
        )
        if result.scalar_one_or_none() is not None:
            log.info("Demo data already exists — skipping seed.")
            return

        # ── 1. Tribe ──────────────────────────────────────────────
        log.info("Creating tribe: Frontier Wolves [WOLF]")
        tribe = Tribe(
            name="Frontier Wolves",
            name_short="WOLF",
            leader_address="0x" + "1" * 40,
            invite_code="WOLF-2026",
        )
        session.add(tribe)
        await session.flush()  # get tribe.id

        # ── 2. Members ────────────────────────────────────────────
        member_specs = [
            ("Asterix", "leader", "Cruiser", "1"),
            ("Kali Anemoi", "officer", "Destroyer", "2"),
            ("Raven Dust", "member", "Frigate", "3"),
            ("Ghost Signal", "recruit", "Hauler", "4"),
        ]
        members: list[Member] = []
        for name, role, ship, digit in member_specs:
            addr = "0x" + digit * 40
            m = Member(
                tribe_id=tribe.id,
                wallet_address=addr,
                character_name=name,
                role=role,
                ship_class=ship,
                last_active=_ts_ago(minutes=random.randint(5, 360)),
                joined_at=_ts_ago(days=random.randint(1, 14)),
            )
            session.add(m)
            members.append(m)
        await session.flush()
        log.info("  Created %d members", len(members))

        # ── 3. Orbital Zones ──────────────────────────────────────
        zone_specs = [
            ("Alpha Nexus", "zone-alpha-1", 0),
            ("Bravo Reach", "zone-bravo-2", 1),
            ("Charlie Void", "zone-charlie-3", 3),
            ("Delta Shroud", "zone-delta-4", 2),
            ("Echo Abyss", "zone-echo-5", 4),
        ]
        zones: list[OrbitalZone] = []
        for zname, zid, tier in zone_specs:
            z = OrbitalZone(
                zone_id=zid,
                name=zname,
                feral_ai_tier=tier,
                last_scanned=_ts_ago(hours=random.randint(0, 12)),
                cycle=CURRENT_CYCLE,
            )
            session.add(z)
            zones.append(z)
        await session.flush()
        log.info("  Created %d orbital zones", len(zones))

        # ── 4. Scans ─────────────────────────────────────────────
        result_types = ["CLEAR", "ANOMALY", "HOSTILE"]
        sig_types = ["EM", "HEAT", "GRAVIMETRIC", "RADAR"]
        scan_count = 0
        for _ in range(13):
            zone = random.choice(zones)
            rt = random.choice(result_types)
            scan = Scan(
                zone_id=zone.id,
                scanner_id=random.choice(members).id,
                result_type=rt,
                signature_type=random.choice(sig_types),
                resolution=random.randint(10, 95),
                confidence=random.randint(40, 100),
                environment=random.choice(
                    ["nebula", "asteroid field", "open space", "debris cloud", None]
                ),
                cycle=CURRENT_CYCLE,
                scanned_at=_ts_ago(
                    hours=random.randint(0, 23), minutes=random.randint(0, 59)
                ),
            )
            session.add(scan)
            scan_count += 1
        log.info("  Created %d scans", scan_count)

        # ── 5. Feral AI Events ────────────────────────────────────
        feral_zones = [z for z in zones if z.feral_ai_tier > 0]
        event_types = ["spawned", "evolved", "critical"]
        feral_count = 0
        for _ in range(6):
            zone = random.choice(feral_zones)
            et = random.choice(event_types)
            prev_tier = max(0, zone.feral_ai_tier - 1)
            new_tier = zone.feral_ai_tier
            evt = FeralAIEvent(
                zone_id=zone.id,
                event_type=et,
                severity=random.randint(1, 5),
                previous_tier=prev_tier,
                new_tier=new_tier,
                cycle=CURRENT_CYCLE,
                timestamp=_ts_ago(hours=random.randint(1, 20)),
            )
            session.add(evt)
            feral_count += 1
        log.info("  Created %d feral AI events", feral_count)

        # ── 6. Killmails ─────────────────────────────────────────
        npc_names = [
            "Vex Marauder",
            "Iron Drifter",
            "Null Phantom",
            "Tera Corsair",
            "Blaze Runner",
            "Omega Sentinel",
            "Void Reaver",
            "Flux Nomad",
            "Arc Wraith",
            "Crimson Fang",
        ]
        wolf_members_info = [
            ("0x" + "1" * 40, "Asterix", "WOLF"),
            ("0x" + "2" * 40, "Kali Anemoi", "WOLF"),
            ("0x" + "3" * 40, "Raven Dust", "WOLF"),
            ("0x" + "4" * 40, "Ghost Signal", "WOLF"),
        ]
        kill_count = 0
        for i in range(12):
            sys_id = random.randint(30000001, 30000020)
            ts = _ts_ago(hours=random.randint(0, 47), minutes=random.randint(0, 59))

            # ~40% chance a WOLF member is the killer, ~20% victim
            roll = random.random()
            if roll < 0.4:
                killer = random.choice(wolf_members_info)
                killer_addr, killer_name, killer_corp = killer[0], killer[1], killer[2]
                victim_name = random.choice(npc_names)
                victim_addr = "0x" + uuid.uuid4().hex[:40]
                victim_corp = random.choice(["RATS", "VOID", "NOVA", None])
            elif roll < 0.6:
                victim = random.choice(wolf_members_info)
                victim_addr, victim_name, victim_corp = victim[0], victim[1], victim[2]
                killer_name = random.choice(npc_names)
                killer_addr = "0x" + uuid.uuid4().hex[:40]
                killer_corp = random.choice(["RATS", "VOID", "NOVA"])
            else:
                killer_name = random.choice(npc_names)
                killer_addr = "0x" + uuid.uuid4().hex[:40]
                killer_corp = random.choice(["RATS", "VOID", "NOVA", None])
                victim_name = random.choice(npc_names)
                victim_addr = "0x" + uuid.uuid4().hex[:40]
                victim_corp = random.choice(["RATS", "VOID", "NOVA", None])

            km = Killmail(
                kill_id=100000 + i,
                victim_address=victim_addr,
                victim_name=victim_name,
                victim_corp_name=victim_corp,
                killer_address=killer_addr,
                killer_name=killer_name,
                killer_corp_name=killer_corp,
                solar_system_id=sys_id,
                timestamp=ts,
                raw_json=json.dumps({"seed": True, "kill_id": 100000 + i}),
                cycle=CURRENT_CYCLE,
            )
            session.add(km)
            kill_count += 1
        log.info("  Created %d killmails", kill_count)

        # ── 7. Production Jobs ────────────────────────────────────
        asterix = members[0]
        kali = members[1]
        raven = members[2]

        jobs = [
            ProductionJob(
                tribe_id=tribe.id,
                created_by=asterix.id,
                assigned_to=raven.id,
                blueprint_name="Aggressive Shell",
                quantity=5,
                status="queued",
                materials_ready=True,
                created_at=_ts_ago(hours=2),
            ),
            ProductionJob(
                tribe_id=tribe.id,
                created_by=kali.id,
                assigned_to=kali.id,
                blueprint_name="Nursery",
                quantity=1,
                status="in_progress",
                materials_ready=True,
                created_at=_ts_ago(hours=6),
            ),
            ProductionJob(
                tribe_id=tribe.id,
                created_by=asterix.id,
                assigned_to=asterix.id,
                blueprint_name="Nest",
                quantity=2,
                status="complete",
                materials_ready=True,
                created_at=_ts_ago(days=1),
                completed_at=_ts_ago(hours=4),
            ),
        ]
        for j in jobs:
            session.add(j)
        log.info("  Created %d production jobs", len(jobs))

        # ── 8. Alert Configs ──────────────────────────────────────
        webhook = "https://discord.com/api/webhooks/demo/seed"
        alerts = [
            AlertConfig(
                tribe_id=tribe.id,
                created_by=asterix.id,
                alert_type="hostile_scan",
                target_name="All Zones",
                discord_webhook_url=webhook,
                enabled=True,
                cooldown_minutes=10,
            ),
            AlertConfig(
                tribe_id=tribe.id,
                created_by=kali.id,
                alert_type="feral_evolved",
                target_name="High-Tier Zones",
                threshold=2,
                discord_webhook_url=webhook,
                enabled=True,
                cooldown_minutes=15,
            ),
        ]
        for a in alerts:
            session.add(a)
        log.info("  Created %d alert configs", len(alerts))

        # ── Commit ────────────────────────────────────────────────
        await session.commit()
        log.info("Demo seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
