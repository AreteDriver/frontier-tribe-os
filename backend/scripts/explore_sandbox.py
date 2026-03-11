"""Probe EVE Frontier World API to confirm field names and response shapes.

One-shot exploration script for hackathon prep. No auth required.
"""

import json
import logging
from typing import Any

import httpx

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://blockchain-gateway-stillness.live.tech.evefrontier.com"

ENDPOINTS: list[tuple[str, str]] = [
    ("health", "/health"),
    ("tribes", "/v2/tribes?limit=5"),
    ("smartcharacters", "/v2/smartcharacters?limit=3"),
    ("smartassemblies", "/v2/smartassemblies?limit=3"),
    ("types", "/v2/types?limit=3"),
    ("killmails", "/v2/killmails?limit=3"),
    ("solarsystems", "/v2/solarsystems?limit=3"),
    ("fuels", "/v2/fuels?limit=3"),
]

TIMEOUT = 10.0


def probe_endpoint(client: httpx.Client, name: str, path: str) -> dict[str, Any]:
    """Hit a single endpoint and return a summary dict."""
    url = f"{BASE_URL}{path}"
    result: dict[str, Any] = {"name": name, "url": url}

    try:
        resp = client.get(url)
        result["status"] = resp.status_code

        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
            return result

        # Try JSON parse
        try:
            data = resp.json()
        except Exception:
            result["error"] = "Response is not JSON"
            result["raw_preview"] = resp.text[:500]
            return result

        # Analyze shape
        if isinstance(data, dict):
            result["top_keys"] = list(data.keys())

            # Look for the list payload — common patterns: root list key or "data" key
            items = None
            for key in data:
                if isinstance(data[key], list) and len(data[key]) > 0:
                    items = data[key]
                    result["list_key"] = key
                    result["list_length"] = len(items)
                    break

            if items:
                first = items[0]
                if isinstance(first, dict):
                    result["item_keys"] = list(first.keys())
                    result["sample"] = first
                else:
                    result["sample"] = first
            else:
                # No list found — dump top-level as sample
                result["sample"] = data

        elif isinstance(data, list):
            result["top_keys"] = ["(root list)"]
            result["list_length"] = len(data)
            if data and isinstance(data[0], dict):
                result["item_keys"] = list(data[0].keys())
                result["sample"] = data[0]
            elif data:
                result["sample"] = data[0]
        else:
            result["sample"] = data

    except httpx.TimeoutException:
        result["status"] = None
        result["error"] = "Timeout"
    except httpx.RequestError as exc:
        result["status"] = None
        result["error"] = f"Request error: {exc}"

    return result


def print_result(r: dict[str, Any]) -> None:
    """Pretty-print a single endpoint result."""
    log.info("=" * 70)
    log.info("ENDPOINT: %s", r["name"])
    log.info("URL:      %s", r["url"])
    log.info("STATUS:   %s", r.get("status", "N/A"))

    if "error" in r:
        log.info("ERROR:    %s", r["error"])
        if "raw_preview" in r:
            log.info("RAW:      %s", r["raw_preview"])
        return

    if "top_keys" in r:
        log.info("TOP KEYS: %s", r["top_keys"])

    if "list_key" in r:
        log.info("LIST KEY: %s  (count: %s)", r["list_key"], r.get("list_length"))

    if "item_keys" in r:
        log.info("ITEM KEYS: %s", r["item_keys"])

    if "sample" in r:
        log.info("SAMPLE:")
        log.info(json.dumps(r["sample"], indent=2, default=str))


def main() -> None:
    results: list[dict[str, Any]] = []

    with httpx.Client(timeout=TIMEOUT) as client:
        for name, path in ENDPOINTS:
            log.info("\nProbing %s ...", name)
            r = probe_endpoint(client, name, path)
            print_result(r)
            results.append(r)

    # Summary
    log.info("\n" + "=" * 70)
    log.info("SUMMARY")
    log.info("=" * 70)

    succeeded = [r for r in results if r.get("status") == 200 and "error" not in r]
    failed = [r for r in results if r not in succeeded]

    log.info("Succeeded (%d):", len(succeeded))
    for r in succeeded:
        log.info("  [200] %s", r["name"])

    if failed:
        log.info("Failed (%d):", len(failed))
        for r in failed:
            status = r.get("status", "???")
            err = r.get("error", "unknown")
            log.info("  [%s] %s — %s", status, r["name"], err)
    else:
        log.info("All endpoints succeeded.")


if __name__ == "__main__":
    main()
