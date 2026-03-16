"""Sui JSON-RPC client for balance and transaction queries.

Talks directly to the Sui fullnode RPC — no SDK needed on Python side.
Wallet signing happens client-side via @mysten/dapp-kit.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def _rpc_call(method: str, params: list) -> dict | None:
    """Make a Sui JSON-RPC 2.0 call."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(settings.sui_rpc_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                logger.warning("Sui RPC error for %s: %s", method, data["error"])
                return None
            return data.get("result")
    except httpx.HTTPError as e:
        logger.warning("Sui RPC call %s failed: %s", method, e)
        return None


async def get_all_balances(address: str) -> list[dict]:
    """suix_getAllBalances — returns all coin balances for an address."""
    result = await _rpc_call("suix_getAllBalances", [address])
    if result is None:
        return []
    return result if isinstance(result, list) else []


async def get_coin_balance(
    address: str, coin_type: str = "0x2::sui::SUI"
) -> dict | None:
    """suix_getBalance — returns balance for a specific coin type."""
    return await _rpc_call("suix_getBalance", [address, coin_type])


async def get_transactions_for_address(address: str, limit: int = 20) -> list[dict]:
    """suix_queryTransactionBlocks — returns recent transactions involving an address.

    Queries transactions where the address is the sender (FromAddress filter).
    """
    query = {"filter": {"FromAddress": address}, "options": {"showEffects": True}}
    result = await _rpc_call("suix_queryTransactionBlocks", [query, None, limit, True])
    if result is None:
        return []
    return result.get("data", []) if isinstance(result, dict) else []


async def get_transaction_details(tx_digest: str) -> dict | None:
    """sui_getTransactionBlock — returns details of a specific transaction."""
    return await _rpc_call(
        "sui_getTransactionBlock",
        [
            tx_digest,
            {"showEffects": True, "showInput": True, "showBalanceChanges": True},
        ],
    )
