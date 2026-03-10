"""Census member role management tests."""


async def _add_second_member(client, tribe_with_leader, second_auth_headers):
    """Helper: add second user to the tribe via join + approve flow."""
    tribe_data, leader_headers = tribe_with_leader
    invite_code = tribe_data["invite_code"]
    await client.post(f"/census/tribes/join/{invite_code}", headers=second_auth_headers)

    requests_resp = await client.get(
        f"/census/tribes/{tribe_data['id']}/requests", headers=leader_headers
    )
    request_id = requests_resp.json()[0]["id"]
    await client.post(
        f"/census/tribes/{tribe_data['id']}/requests/{request_id}",
        json={"action": "approve"},
        headers=leader_headers,
    )

    members_resp = await client.get(
        f"/census/tribes/{tribe_data['id']}/members", headers=leader_headers
    )
    members = members_resp.json()
    second_member = next(m for m in members if m["character_name"] == "SecondPilot")
    return tribe_data, leader_headers, second_member


async def test_update_role_to_member(client, tribe_with_leader, second_auth_headers):
    tribe_data, leader_headers, second_member = await _add_second_member(
        client, tribe_with_leader, second_auth_headers
    )
    resp = await client.patch(
        f"/census/tribes/{tribe_data['id']}/members/{second_member['id']}/role",
        json={"role": "member"},
        headers=leader_headers,
    )
    assert resp.status_code == 200
    assert "member" in resp.json()["detail"]


async def test_update_role_to_officer(client, tribe_with_leader, second_auth_headers):
    tribe_data, leader_headers, second_member = await _add_second_member(
        client, tribe_with_leader, second_auth_headers
    )
    resp = await client.patch(
        f"/census/tribes/{tribe_data['id']}/members/{second_member['id']}/role",
        json={"role": "officer"},
        headers=leader_headers,
    )
    assert resp.status_code == 200


async def test_update_role_invalid_role_rejected(
    client, tribe_with_leader, second_auth_headers
):
    tribe_data, leader_headers, second_member = await _add_second_member(
        client, tribe_with_leader, second_auth_headers
    )
    resp = await client.patch(
        f"/census/tribes/{tribe_data['id']}/members/{second_member['id']}/role",
        json={"role": "emperor"},
        headers=leader_headers,
    )
    assert resp.status_code == 422  # Pydantic rejects invalid Literal value


async def test_cannot_demote_leader(client, tribe_with_leader, second_auth_headers):
    tribe_data, leader_headers = tribe_with_leader
    # Get leader's member ID
    members_resp = await client.get(
        f"/census/tribes/{tribe_data['id']}/members", headers=leader_headers
    )
    leader = members_resp.json()[0]

    resp = await client.patch(
        f"/census/tribes/{tribe_data['id']}/members/{leader['id']}/role",
        json={"role": "member"},
        headers=leader_headers,
    )
    assert resp.status_code == 400
    assert "Cannot demote" in resp.json()["detail"]


async def test_officer_cannot_promote_to_officer(
    client, tribe_with_leader, second_auth_headers
):
    """Only leaders can promote to officer. Officers cannot."""
    tribe_data, leader_headers, second_member = await _add_second_member(
        client, tribe_with_leader, second_auth_headers
    )
    # Promote second to officer first
    await client.patch(
        f"/census/tribes/{tribe_data['id']}/members/{second_member['id']}/role",
        json={"role": "officer"},
        headers=leader_headers,
    )

    # Create a third member
    resp3 = await client.post("/auth/dev-login?name=ThirdPilot")
    headers3 = {"Authorization": f"Bearer {resp3.json()['access_token']}"}
    invite_code = tribe_data["invite_code"]
    await client.post(f"/census/tribes/join/{invite_code}", headers=headers3)

    requests_resp = await client.get(
        f"/census/tribes/{tribe_data['id']}/requests", headers=leader_headers
    )
    req_id = requests_resp.json()[0]["id"]
    await client.post(
        f"/census/tribes/{tribe_data['id']}/requests/{req_id}",
        json={"action": "approve"},
        headers=leader_headers,
    )

    members_resp = await client.get(
        f"/census/tribes/{tribe_data['id']}/members", headers=leader_headers
    )
    third = next(m for m in members_resp.json() if m["character_name"] == "ThirdPilot")

    # Officer tries to promote third to officer — should fail
    resp = await client.patch(
        f"/census/tribes/{tribe_data['id']}/members/{third['id']}/role",
        json={"role": "officer"},
        headers=second_auth_headers,
    )
    assert resp.status_code == 403
