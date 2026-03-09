"""Census tribe CRUD tests."""

import uuid


async def test_create_tribe(client, auth_headers):
    resp = await client.post(
        "/census/tribes",
        json={"name": "Wolfpack", "name_short": "WOLF"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Wolfpack"
    assert data["name_short"] == "WOLF"
    assert data["member_count"] == 1
    assert data["invite_code"] is not None


async def test_create_tribe_sets_leader_role(client, auth_headers):
    resp = await client.post(
        "/census/tribes",
        json={"name": "LeaderTest"},
        headers=auth_headers,
    )
    tribe_id = resp.json()["id"]
    members_resp = await client.get(
        f"/census/tribes/{tribe_id}/members", headers=auth_headers
    )
    members = members_resp.json()
    assert len(members) == 1
    assert members[0]["role"] == "leader"


async def test_create_second_tribe_fails(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    resp = await client.post(
        "/census/tribes",
        json={"name": "SecondTribe"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "already in a tribe" in resp.json()["detail"]


async def test_get_tribe(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    resp = await client.get(f"/census/tribes/{tribe_data['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "TestTribe"


async def test_get_tribe_not_found(client, auth_headers):
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/census/tribes/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


async def test_get_tribe_hides_invite_code_for_non_member(
    client, tribe_with_leader, second_auth_headers
):
    tribe_data, _ = tribe_with_leader
    resp = await client.get(
        f"/census/tribes/{tribe_data['id']}", headers=second_auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["invite_code"] is None


async def test_list_members(client, tribe_with_leader):
    tribe_data, headers = tribe_with_leader
    resp = await client.get(
        f"/census/tribes/{tribe_data['id']}/members", headers=headers
    )
    assert resp.status_code == 200
    members = resp.json()
    assert len(members) == 1
    assert members[0]["character_name"] == "TestPilot"


async def test_list_members_forbidden_for_non_member(
    client, tribe_with_leader, second_auth_headers
):
    tribe_data, _ = tribe_with_leader
    resp = await client.get(
        f"/census/tribes/{tribe_data['id']}/members", headers=second_auth_headers
    )
    assert resp.status_code == 403
