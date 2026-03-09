from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BalanceResponse(BaseModel):
    coin_type: str
    total_balance: str  # String for large ints
    coin_object_count: int


class WalletBalancesResponse(BaseModel):
    address: str
    balances: list[BalanceResponse]


class TransactionResponse(BaseModel):
    id: UUID
    tx_digest: str
    from_address: str
    to_address: str
    amount: str
    coin_type: str
    memo: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TransferRecord(BaseModel):
    """Client sends this after signing tx on frontend. Backend records it."""

    tx_digest: str
    to_address: str
    amount: str
    coin_type: str = "0x2::sui::SUI"
    memo: str | None = None
