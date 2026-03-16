"""Sui RPC client unit tests (mocked httpx)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.api.sui import get_all_balances, get_coin_balance, get_transactions_for_address


def _mock_httpx_client(json_response):
    """Create a mock httpx.AsyncClient that returns given JSON."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = json_response

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


@patch("app.api.sui.httpx.AsyncClient")
async def test_get_all_balances_success(mock_client_cls):
    mock_client_cls.return_value = _mock_httpx_client(
        {
            "jsonrpc": "2.0",
            "result": [
                {
                    "coinType": "0x2::sui::SUI",
                    "totalBalance": "1000",
                    "coinObjectCount": 1,
                }
            ],
        }
    )
    result = await get_all_balances("0xabc")
    assert len(result) == 1
    assert result[0]["coinType"] == "0x2::sui::SUI"


@patch("app.api.sui.httpx.AsyncClient")
async def test_get_all_balances_rpc_error(mock_client_cls):
    mock_client_cls.return_value = _mock_httpx_client(
        {
            "jsonrpc": "2.0",
            "error": {"code": -32000, "message": "fail"},
        }
    )
    result = await get_all_balances("0xbad")
    assert result == []


@patch("app.api.sui.httpx.AsyncClient")
async def test_get_all_balances_network_error(mock_client_cls):
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.ConnectError("connection refused")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    result = await get_all_balances("0xfail")
    assert result == []


@patch("app.api.sui.httpx.AsyncClient")
async def test_get_coin_balance(mock_client_cls):
    mock_client_cls.return_value = _mock_httpx_client(
        {
            "jsonrpc": "2.0",
            "result": {"coinType": "0x2::sui::SUI", "totalBalance": "5000"},
        }
    )
    result = await get_coin_balance("0xabc")
    assert result["totalBalance"] == "5000"


@patch("app.api.sui.httpx.AsyncClient")
async def test_get_transactions_for_address(mock_client_cls):
    mock_client_cls.return_value = _mock_httpx_client(
        {
            "jsonrpc": "2.0",
            "result": {"data": [{"digest": "tx1"}, {"digest": "tx2"}]},
        }
    )
    result = await get_transactions_for_address("0xabc")
    assert len(result) == 2
