"""Health endpoint tests."""


async def test_health_returns_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "frontier-tribe-os"


async def test_ledger_status(client):
    resp = await client.get("/ledger/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
