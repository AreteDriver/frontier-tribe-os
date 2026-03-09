"""World API client unit tests (mocked httpx)."""

from unittest.mock import AsyncMock, MagicMock, patch

from app.api.frontier import get_character, get_item_types, get_tribes


def _mock_httpx_client(json_response=None, side_effect=None):
    """Create a mock httpx.AsyncClient."""
    mock_client = AsyncMock()
    if side_effect:
        mock_client.get.side_effect = side_effect
    else:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = json_response
        mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


@patch("app.api.frontier.httpx.AsyncClient")
async def test_get_character_success(mock_client_cls):
    mock_client_cls.return_value = _mock_httpx_client(
        {"name": "TestChar", "address": "0xabc"}
    )
    result = await get_character("0xabc")
    assert result["name"] == "TestChar"


@patch("app.api.frontier.httpx.AsyncClient")
async def test_get_character_failure_returns_none(mock_client_cls):
    mock_client_cls.return_value = _mock_httpx_client(side_effect=Exception("timeout"))
    result = await get_character("0xfail")
    assert result is None


@patch("app.api.frontier.httpx.AsyncClient")
async def test_get_item_types_falls_back_to_static(mock_client_cls):
    mock_client_cls.return_value = _mock_httpx_client(side_effect=Exception("API down"))
    result = await get_item_types()
    assert isinstance(result, list)


@patch("app.api.frontier.httpx.AsyncClient")
async def test_get_tribes_success(mock_client_cls):
    mock_client_cls.return_value = _mock_httpx_client([{"id": 1, "name": "Wolves"}])
    result = await get_tribes()
    assert len(result) == 1
    assert result[0]["name"] == "Wolves"


@patch("app.api.frontier.httpx.AsyncClient")
async def test_get_tribes_failure_returns_empty(mock_client_cls):
    mock_client_cls.return_value = _mock_httpx_client(side_effect=Exception("down"))
    result = await get_tribes()
    assert result == []
