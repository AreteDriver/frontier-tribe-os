"""Tests for the Forge gap analysis endpoint."""

import pytest


@pytest.mark.asyncio
async def test_gap_analysis_empty(client, tribe_with_leader):
    """No jobs → empty gap analysis."""
    tribe, headers = tribe_with_leader
    resp = await client.get(
        f"/forge/tribes/{tribe['id']}/gap-analysis", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_jobs"] == 0
    assert data["jobs_materials_ready"] == 0
    assert data["jobs_blocked"] == 0
    assert data["material_gaps"] == []


@pytest.mark.asyncio
async def test_gap_analysis_with_jobs_and_no_inventory(client, tribe_with_leader):
    """Jobs with known blueprints but no inventory → all materials are deficits."""
    tribe, headers = tribe_with_leader

    # Create a job using a known blueprint from blueprints.json
    await client.post(
        f"/forge/tribes/{tribe['id']}/jobs",
        json={"blueprint_name": "bp_smartassembly_gatehouse", "quantity": 1},
        headers=headers,
    )

    resp = await client.get(
        f"/forge/tribes/{tribe['id']}/gap-analysis", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_jobs"] == 1
    assert data["jobs_materials_ready"] == 0
    assert len(data["material_gaps"]) > 0

    # Every gap should have deficit == required (nothing held)
    for gap in data["material_gaps"]:
        assert gap["deficit"] == gap["required"]
        assert gap["held"] == 0


@pytest.mark.asyncio
async def test_gap_analysis_with_partial_inventory(client, tribe_with_leader):
    """Partial inventory reduces deficit but doesn't eliminate it."""
    tribe, headers = tribe_with_leader

    # Create a gatehouse job (needs 500 Iron, 200 Copper, 100 Silicon)
    await client.post(
        f"/forge/tribes/{tribe['id']}/jobs",
        json={"blueprint_name": "bp_smartassembly_gatehouse", "quantity": 1},
        headers=headers,
    )

    # Add partial iron inventory
    await client.put(
        f"/forge/tribes/{tribe['id']}/inventory",
        json={"item_id": 1, "item_name": "Iron", "quantity": 300},
        headers=headers,
    )

    resp = await client.get(
        f"/forge/tribes/{tribe['id']}/gap-analysis", headers=headers
    )
    data = resp.json()
    assert data["total_jobs"] == 1
    # Should still have gaps (iron partially covered, copper/silicon missing)
    assert len(data["material_gaps"]) >= 2


@pytest.mark.asyncio
async def test_gap_analysis_unknown_blueprint(client, tribe_with_leader):
    """Jobs with unknown blueprint names are skipped in gap analysis."""
    tribe, headers = tribe_with_leader

    await client.post(
        f"/forge/tribes/{tribe['id']}/jobs",
        json={"blueprint_name": "unknown_blueprint_xyz", "quantity": 1},
        headers=headers,
    )

    resp = await client.get(
        f"/forge/tribes/{tribe['id']}/gap-analysis", headers=headers
    )
    data = resp.json()
    assert data["total_jobs"] == 1
    assert data["material_gaps"] == []


@pytest.mark.asyncio
async def test_gap_analysis_forbidden(client, tribe_with_leader, second_auth_headers):
    """Non-member can't access gap analysis."""
    tribe, _ = tribe_with_leader
    resp = await client.get(
        f"/forge/tribes/{tribe['id']}/gap-analysis", headers=second_auth_headers
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_blueprints_endpoint(client, auth_headers):
    """Blueprints endpoint returns static data."""
    resp = await client.get("/forge/blueprints", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "type_id" in data[0]
    assert "materials" in data[0]
