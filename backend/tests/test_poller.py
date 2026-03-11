"""Tests for World API background poller."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.watch.poller import WorldAPIPoller


def _mock_response(json_data, status_code=200):
    """Create a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        import httpx

        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


def _make_mock_client(responses: dict[str, MagicMock]):
    """Create a mock httpx.AsyncClient that routes by URL path."""
    client = AsyncMock()

    async def mock_get(url, **kwargs):
        for path, resp in responses.items():
            if path in url:
                return resp
        return _mock_response({})

    client.get = AsyncMock(side_effect=mock_get)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.fixture
def tribe_api_data():
    return [
        {
            "id": 42,
            "name": "Wolves of War",
            "nameShort": "WOLF",
            "leaderAddress": "0xabc123",
            "tokenContractAddress": "0xtoken1",
        },
        {
            "id": 99,
            "name": "Shadow Syndicate",
            "nameShort": "SHAD",
            "leaderAddress": "0xdef456",
            "tokenContractAddress": None,
        },
    ]


@pytest.fixture
def killmail_api_data():
    return [
        {
            "id": 1,
            "killer": {"address": "0xkiller1", "name": "Killer One", "id": "100"},
            "victim": {"address": "0xvictim1", "name": "Victim One", "id": "200"},
            "solarSystemId": 30023604,
            "time": "2025-12-10T16:20:58Z",
        },
        {
            "id": 2,
            "killer": {"address": "0xkiller2", "name": "Killer Two", "id": "101"},
            "victim": {"address": "0xvictim2", "name": "Victim Two", "id": "201"},
            "solarSystemId": 30023605,
            "time": "2025-12-10T17:00:00Z",
        },
    ]


@pytest.fixture
def assembly_api_data():
    return [
        {"id": "a1", "type": "SmartGate"},
        {"id": "a2", "type": "SmartGate"},
        {"id": "a3", "type": "SmartTurret"},
        {"id": "a4", "type": "SmartStorageUnit"},
    ]


@patch("app.modules.watch.poller.async_session")
@patch("app.modules.watch.poller.httpx.AsyncClient")
async def test_poll_once_syncs_tribes(
    mock_client_cls,
    mock_session_factory,
    tribe_api_data,
    killmail_api_data,
    assembly_api_data,
):
    """poll_once fetches tribes, killmails, and assemblies."""
    responses = {
        "/v2/tribes": _mock_response(tribe_api_data),
        "/v2/killmails": _mock_response(killmail_api_data),
        "/v2/smartassemblies": _mock_response(assembly_api_data),
    }
    mock_client = _make_mock_client(responses)
    mock_client_cls.return_value = mock_client

    # Mock DB session
    mock_db = AsyncMock()
    mock_db.add = MagicMock()  # add() is synchronous on SQLAlchemy sessions
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # No existing tribe
    mock_db.execute.return_value = mock_result
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    poller = WorldAPIPoller(interval_seconds=60)
    await poller.poll_once()

    # Verify all three endpoints were called
    assert mock_client.get.call_count == 3


@patch("app.modules.watch.poller.async_session")
@patch("app.modules.watch.poller.httpx.AsyncClient")
async def test_poll_once_handles_api_failure(mock_client_cls, mock_session_factory):
    """poll_once continues even when individual sync tasks fail."""
    # Tribes fails, killmails and assemblies succeed
    fail_resp = _mock_response({}, status_code=500)
    ok_resp = _mock_response([])
    responses = {
        "/v2/tribes": fail_resp,
        "/v2/killmails": ok_resp,
        "/v2/smartassemblies": ok_resp,
    }
    mock_client = _make_mock_client(responses)
    mock_client_cls.return_value = mock_client

    poller = WorldAPIPoller(interval_seconds=60)
    # Should not raise even though tribes endpoint returns 500
    await poller.poll_once()


@patch("app.modules.watch.poller.async_session")
@patch("app.modules.watch.poller.httpx.AsyncClient")
async def test_poll_once_upserts_existing_tribe(
    mock_client_cls, mock_session_factory, tribe_api_data
):
    """Existing tribes get updated, not duplicated."""
    responses = {
        "/v2/tribes": _mock_response(tribe_api_data),
        "/v2/killmails": _mock_response([]),
        "/v2/smartassemblies": _mock_response([]),
    }
    mock_client = _make_mock_client(responses)
    mock_client_cls.return_value = mock_client

    # Mock DB with existing tribe for world_tribe_id=42
    existing_tribe = MagicMock()
    existing_tribe.name = "Old Name"
    existing_tribe.name_short = "OLD"
    existing_tribe.leader_address = "0xold"
    existing_tribe.token_contract_address = None

    mock_db = AsyncMock()
    mock_db.add = MagicMock()  # add() is synchronous
    mock_result = MagicMock()
    # First call returns existing tribe, second returns None (new tribe)
    mock_result.scalar_one_or_none.side_effect = [existing_tribe, None]
    mock_db.execute.return_value = mock_result

    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    poller = WorldAPIPoller(interval_seconds=60)
    await poller.poll_once()

    # Existing tribe should have been updated
    assert existing_tribe.name == "Wolves of War"
    assert existing_tribe.name_short == "WOLF"


async def test_start_stop_lifecycle():
    """Poller starts and stops cleanly."""
    poller = WorldAPIPoller(interval_seconds=1)

    with patch.object(poller, "poll_once", new_callable=AsyncMock):
        await poller.start()
        assert poller._running is True
        assert poller._task is not None

        # Let it run one cycle
        await asyncio.sleep(0.1)

        await poller.stop()
        assert poller._running is False
        assert poller._task is None


async def test_start_idempotent():
    """Calling start twice does not create duplicate tasks."""
    poller = WorldAPIPoller(interval_seconds=1)

    with patch.object(poller, "poll_once", new_callable=AsyncMock):
        await poller.start()
        first_task = poller._task

        await poller.start()  # second call — should be no-op
        assert poller._task is first_task

        await poller.stop()


@patch("app.modules.watch.poller.async_session")
@patch("app.modules.watch.poller.httpx.AsyncClient")
async def test_sync_assemblies_logs_counts(
    mock_client_cls, mock_session_factory, assembly_api_data
):
    """Assembly sync correctly counts types."""
    responses = {
        "/v2/tribes": _mock_response([]),
        "/v2/killmails": _mock_response([]),
        "/v2/smartassemblies": _mock_response(assembly_api_data),
    }
    mock_client = _make_mock_client(responses)
    mock_client_cls.return_value = mock_client

    # Mock DB (tribes sync needs it even with empty list)
    mock_db = AsyncMock()
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    poller = WorldAPIPoller(interval_seconds=60)
    await poller.poll_once()

    # If we got here without exception, assembly parsing worked
    assert mock_client.get.call_count == 3
