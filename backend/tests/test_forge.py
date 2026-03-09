"""Forge module tests — jobs and inventory."""

import uuid


async def test_create_job(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    resp = await client.post(
        f"/forge/tribes/{tribe_data['id']}/jobs",
        json={"blueprint_name": "Fighter Ship", "quantity": 5},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["blueprint_name"] == "Fighter Ship"
    assert data["quantity"] == 5
    assert data["status"] == "queued"
    assert data["materials_ready"] is False


async def test_create_job_defaults(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    resp = await client.post(
        f"/forge/tribes/{tribe_data['id']}/jobs",
        json={"blueprint_name": "Gatehouse"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 1


async def test_list_jobs(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    await client.post(
        f"/forge/tribes/{tribe_data['id']}/jobs",
        json={"blueprint_name": "Item A"},
        headers=headers,
    )
    await client.post(
        f"/forge/tribes/{tribe_data['id']}/jobs",
        json={"blueprint_name": "Item B"},
        headers=headers,
    )
    resp = await client.get(f"/forge/tribes/{tribe_data['id']}/jobs", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_list_jobs_filter_by_status(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    create_resp = await client.post(
        f"/forge/tribes/{tribe_data['id']}/jobs",
        json={"blueprint_name": "Filtered"},
        headers=headers,
    )
    job_id = create_resp.json()["id"]
    await client.patch(
        f"/forge/tribes/{tribe_data['id']}/jobs/{job_id}",
        json={"status": "in_progress"},
        headers=headers,
    )

    resp = await client.get(
        f"/forge/tribes/{tribe_data['id']}/jobs?status_filter=in_progress",
        headers=headers,
    )
    assert resp.status_code == 200
    assert all(j["status"] == "in_progress" for j in resp.json())


async def test_update_job_status(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    create_resp = await client.post(
        f"/forge/tribes/{tribe_data['id']}/jobs",
        json={"blueprint_name": "Update Me"},
        headers=headers,
    )
    job_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/forge/tribes/{tribe_data['id']}/jobs/{job_id}",
        json={"status": "blocked"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "blocked"


async def test_update_job_to_complete_sets_timestamp(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    create_resp = await client.post(
        f"/forge/tribes/{tribe_data['id']}/jobs",
        json={"blueprint_name": "Complete Me"},
        headers=headers,
    )
    job_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/forge/tribes/{tribe_data['id']}/jobs/{job_id}",
        json={"status": "complete"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["completed_at"] is not None


async def test_update_job_invalid_status(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    create_resp = await client.post(
        f"/forge/tribes/{tribe_data['id']}/jobs",
        json={"blueprint_name": "Bad Status"},
        headers=headers,
    )
    job_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/forge/tribes/{tribe_data['id']}/jobs/{job_id}",
        json={"status": "destroyed"},
        headers=headers,
    )
    assert resp.status_code == 400


async def test_delete_job(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    create_resp = await client.post(
        f"/forge/tribes/{tribe_data['id']}/jobs",
        json={"blueprint_name": "Delete Me"},
        headers=headers,
    )
    job_id = create_resp.json()["id"]

    resp = await client.delete(
        f"/forge/tribes/{tribe_data['id']}/jobs/{job_id}", headers=headers
    )
    assert resp.status_code == 204


async def test_delete_job_not_found(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    fake_id = str(uuid.uuid4())
    resp = await client.delete(
        f"/forge/tribes/{tribe_data['id']}/jobs/{fake_id}", headers=headers
    )
    assert resp.status_code == 404


async def test_job_forbidden_for_non_member(
    client, tribe_with_leader, second_auth_headers
):
    tribe_data, _ = tribe_with_leader
    resp = await client.get(
        f"/forge/tribes/{tribe_data['id']}/jobs", headers=second_auth_headers
    )
    assert resp.status_code == 403


# Inventory tests


async def test_upsert_inventory_creates_new(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    resp = await client.put(
        f"/forge/tribes/{tribe_data['id']}/inventory",
        json={"item_id": 101, "item_name": "Iron Ore", "quantity": 500},
        headers=headers,
    )
    assert resp.status_code == 200


async def test_upsert_inventory_updates_existing(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    await client.put(
        f"/forge/tribes/{tribe_data['id']}/inventory",
        json={"item_id": 102, "item_name": "Copper", "quantity": 100},
        headers=headers,
    )
    resp = await client.put(
        f"/forge/tribes/{tribe_data['id']}/inventory",
        json={"item_id": 102, "item_name": "Copper", "quantity": 300},
        headers=headers,
    )
    assert resp.status_code == 200

    inv_resp = await client.get(
        f"/forge/tribes/{tribe_data['id']}/inventory", headers=headers
    )
    items = inv_resp.json()
    copper = next(i for i in items if i["item_id"] == 102)
    assert copper["quantity"] == 300


async def test_list_inventory(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    await client.put(
        f"/forge/tribes/{tribe_data['id']}/inventory",
        json={"item_id": 201, "item_name": "Silicon", "quantity": 50},
        headers=headers,
    )
    resp = await client.get(
        f"/forge/tribes/{tribe_data['id']}/inventory", headers=headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_inventory_forbidden_for_non_member(
    client, tribe_with_leader, second_auth_headers
):
    tribe_data, _ = tribe_with_leader
    resp = await client.get(
        f"/forge/tribes/{tribe_data['id']}/inventory", headers=second_auth_headers
    )
    assert resp.status_code == 403
