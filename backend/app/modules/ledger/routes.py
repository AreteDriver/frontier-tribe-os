"""Ledger module — Token treasury (Week 3).

Stub routes. Will integrate Sui TypeScript SDK via a sidecar or direct RPC calls.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("/status")
async def ledger_status():
    return {"status": "not_implemented", "detail": "Ledger module ships in Week 3"}
