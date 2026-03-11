"""Tests for the Ledger treasury summary endpoint."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_treasury_summary(client, tribe_with_leader):
    """Treasury summary returns aggregate data."""
    tribe, headers = tribe_with_leader

    with patch("app.modules.ledger.routes.sui") as mock_sui:
        mock_sui.get_all_balances = AsyncMock(
            return_value=[
                {
                    "coinType": "0x2::sui::SUI",
                    "totalBalance": "1000000000",
                    "coinObjectCount": 1,
                }
            ]
        )

        resp = await client.get(
            f"/ledger/tribes/{tribe['id']}/summary", headers=headers
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["tribe_name"] == "TestTribe"
    assert data["member_count"] == 1
    assert data["total_transactions"] == 0
    assert isinstance(data["treasury_balances"], list)
    assert isinstance(data["members_with_balances"], list)


@pytest.mark.asyncio
async def test_treasury_summary_no_treasury_address(client, auth_headers):
    """Tribe with no leader_address still returns summary (empty treasury)."""
    # Create tribe (dev-login wallet is set but might not have real balances)
    resp = await client.post(
        "/census/tribes",
        json={"name": "NoTreasury", "name_short": "NT"},
        headers=auth_headers,
    )
    tribe = resp.json()

    with patch("app.modules.ledger.routes.sui") as mock_sui:
        mock_sui.get_all_balances = AsyncMock(return_value=[])

        resp = await client.get(
            f"/ledger/tribes/{tribe['id']}/summary", headers=auth_headers
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["member_count"] == 1


@pytest.mark.asyncio
async def test_treasury_summary_forbidden(
    client, tribe_with_leader, second_auth_headers
):
    """Non-member can't access treasury summary."""
    tribe, _ = tribe_with_leader
    resp = await client.get(
        f"/ledger/tribes/{tribe['id']}/summary", headers=second_auth_headers
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_treasury_summary_sui_failure(client, tribe_with_leader):
    """Sui RPC failure is handled gracefully."""
    tribe, headers = tribe_with_leader

    with patch("app.modules.ledger.routes.sui") as mock_sui:
        mock_sui.get_all_balances = AsyncMock(side_effect=Exception("RPC timeout"))

        resp = await client.get(
            f"/ledger/tribes/{tribe['id']}/summary", headers=headers
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["treasury_balances"] == []
    assert data["members_with_balances"] == []
