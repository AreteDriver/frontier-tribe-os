"""One-shot script to pull live killmails and tribes from the EVE Frontier World API.

Read-only exploration — no database writes. Saves raw killmail JSON for reference.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

WORLD_API_BASE = "https://blockchain-gateway-stillness.live.tech.evefrontier.com"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TIMEOUT = 15


def pull_killmails(client: httpx.Client) -> list:
    """Fetch recent killmails from World API."""
    print("=" * 60)
    print("KILLMAILS — /v2/killmails?limit=50")
    print("=" * 60)

    resp = client.get("/v2/killmails", params={"limit": 50})
    resp.raise_for_status()
    raw = resp.json()

    # API may wrap in {"data": [...]} or return bare list
    killmails = raw.get("data", raw) if isinstance(raw, dict) else raw

    print(f"\nTotal killmails returned: {len(killmails)}\n")

    if not killmails:
        print("  (none)")
        return killmails

    for km in killmails:
        kill_id = km.get("id", "?")
        victim = km.get("victim", {})
        killer = km.get("killer", {})
        victim_name = victim.get("name") or victim.get("address", "unknown")[:16]
        killer_name = killer.get("name") or killer.get("address", "unknown")[:16]
        solar_system = km.get("solarSystemId", "?")
        time_str = km.get("time", "?")

        print(f"  Kill #{kill_id}")
        print(f"    Victim:  {victim_name}")
        print(f"    Killer:  {killer_name}")
        print(f"    System:  {solar_system}")
        print(f"    Time:    {time_str}")
        print()

    # Save raw JSON
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    outfile = DATA_DIR / "killmails_sample.json"
    outfile.write_text(json.dumps(raw, indent=2))
    print(f"Raw JSON saved to: {outfile}")

    return killmails


def pull_tribes(client: httpx.Client) -> list:
    """Fetch tribes from World API."""
    print("\n" + "=" * 60)
    print("TRIBES — /v2/tribes?limit=20")
    print("=" * 60)

    resp = client.get("/v2/tribes", params={"limit": 20})
    resp.raise_for_status()
    raw = resp.json()

    tribes = raw.get("data", raw) if isinstance(raw, dict) else raw

    print(f"\nTotal tribes returned: {len(tribes)}\n")

    if not tribes:
        print("  (none)")
        return tribes

    for t in tribes:
        tribe_id = t.get("id", "?")
        name = t.get("name", "unnamed")
        short = t.get("nameShort", "")
        leader = t.get("leaderAddress", "?")
        short_str = f" [{short}]" if short else ""
        leader_short = leader[:16] + "..." if leader and len(leader) > 16 else leader

        print(f"  Tribe #{tribe_id}: {name}{short_str}")
        print(f"    Leader: {leader_short}")
        print()

    return tribes


def main() -> int:
    print(f"EVE Frontier World API Explorer — {datetime.now(timezone.utc).isoformat()}")
    print(f"Base URL: {WORLD_API_BASE}\n")

    try:
        with httpx.Client(base_url=WORLD_API_BASE, timeout=TIMEOUT) as client:
            pull_killmails(client)
            pull_tribes(client)
    except httpx.HTTPStatusError as e:
        print(f"\nHTTP error: {e.response.status_code} — {e.response.text[:200]}")
        return 1
    except httpx.ConnectError as e:
        print(f"\nConnection failed: {e}")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
