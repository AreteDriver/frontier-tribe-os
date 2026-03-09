"""Ledger module tests."""

from unittest.mock import AsyncMock, patch


async def test_ledger_status(client):
    resp = await client.get("/ledger/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@patch("app.modules.ledger.routes.sui.get_all_balances", new_callable=AsyncMock)
async def test_get_tribe_balances(mock_balances, client, tribe_with_leader):
    mock_balances.return_value = [
        {
            "coinType": "0x2::sui::SUI",
            "totalBalance": "5000000000",
            "coinObjectCount": 2,
        }
    ]
    tribe_data, headers = tribe_with_leader
    resp = await client.get(
        f"/ledger/tribes/{tribe_data['id']}/balances", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["balances"]) == 1
    assert data["balances"][0]["total_balance"] == "5000000000"


@patch("app.modules.ledger.routes.sui.get_all_balances", new_callable=AsyncMock)
async def test_get_tribe_balances_empty(mock_balances, client, tribe_with_leader):
    mock_balances.return_value = []
    tribe_data, headers = tribe_with_leader
    resp = await client.get(
        f"/ledger/tribes/{tribe_data['id']}/balances", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["balances"] == []


@patch("app.modules.ledger.routes.sui.get_all_balances", new_callable=AsyncMock)
async def test_get_my_balances(mock_balances, client, auth_headers):
    mock_balances.return_value = [
        {
            "coinType": "0x2::sui::SUI",
            "totalBalance": "1000000000",
            "coinObjectCount": 1,
        }
    ]
    resp = await client.get("/ledger/members/me/balances", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["balances"]) == 1


async def test_get_tribe_balances_forbidden(
    client, tribe_with_leader, second_auth_headers
):
    tribe_data, _ = tribe_with_leader
    resp = await client.get(
        f"/ledger/tribes/{tribe_data['id']}/balances", headers=second_auth_headers
    )
    assert resp.status_code == 403


async def test_record_transaction(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    resp = await client.post(
        f"/ledger/tribes/{tribe_data['id']}/transactions",
        json={
            "tx_digest": "ABC123XYZ",
            "to_address": "0xrecipient",
            "amount": "1000000000",
            "memo": "Test payment",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["tx_digest"] == "ABC123XYZ"
    assert data["amount"] == "1000000000"
    assert data["memo"] == "Test payment"
    assert data["status"] == "confirmed"


async def test_record_duplicate_transaction_fails(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    body = {"tx_digest": "DUPE123", "to_address": "0xrecipient", "amount": "500"}
    await client.post(
        f"/ledger/tribes/{tribe_data['id']}/transactions", json=body, headers=headers
    )
    resp = await client.post(
        f"/ledger/tribes/{tribe_data['id']}/transactions", json=body, headers=headers
    )
    assert resp.status_code == 409


async def test_list_transactions(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    await client.post(
        f"/ledger/tribes/{tribe_data['id']}/transactions",
        json={"tx_digest": "TX001", "to_address": "0xa", "amount": "100"},
        headers=headers,
    )
    await client.post(
        f"/ledger/tribes/{tribe_data['id']}/transactions",
        json={"tx_digest": "TX002", "to_address": "0xb", "amount": "200"},
        headers=headers,
    )
    resp = await client.get(
        f"/ledger/tribes/{tribe_data['id']}/transactions", headers=headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_list_transactions_empty(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    resp = await client.get(
        f"/ledger/tribes/{tribe_data['id']}/transactions", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json() == []
