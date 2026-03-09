"""Census join request workflow tests."""


async def test_request_join_via_invite_code(
    client, tribe_with_leader, second_auth_headers
):
    tribe_data, _ = tribe_with_leader
    invite_code = tribe_data["invite_code"]
    resp = await client.post(
        f"/census/tribes/join/{invite_code}", headers=second_auth_headers
    )
    assert resp.status_code == 201
    assert "Join request submitted" in resp.json()["detail"]


async def test_request_join_invalid_code(client, second_auth_headers):
    resp = await client.post(
        "/census/tribes/join/bogus-code", headers=second_auth_headers
    )
    assert resp.status_code == 404


async def test_request_join_duplicate_rejected(
    client, tribe_with_leader, second_auth_headers
):
    tribe_data, _ = tribe_with_leader
    invite_code = tribe_data["invite_code"]
    await client.post(f"/census/tribes/join/{invite_code}", headers=second_auth_headers)
    resp = await client.post(
        f"/census/tribes/join/{invite_code}", headers=second_auth_headers
    )
    assert resp.status_code == 400
    assert "already pending" in resp.json()["detail"]


async def test_list_join_requests(client, tribe_with_leader, second_auth_headers):
    tribe_data, leader_headers = tribe_with_leader
    invite_code = tribe_data["invite_code"]
    await client.post(f"/census/tribes/join/{invite_code}", headers=second_auth_headers)

    resp = await client.get(
        f"/census/tribes/{tribe_data['id']}/requests", headers=leader_headers
    )
    assert resp.status_code == 200
    requests = resp.json()
    assert len(requests) == 1
    assert requests[0]["status"] == "pending"


async def test_approve_join_request(client, tribe_with_leader, second_auth_headers):
    tribe_data, leader_headers = tribe_with_leader
    invite_code = tribe_data["invite_code"]
    await client.post(f"/census/tribes/join/{invite_code}", headers=second_auth_headers)

    # Get the request ID
    requests_resp = await client.get(
        f"/census/tribes/{tribe_data['id']}/requests", headers=leader_headers
    )
    request_id = requests_resp.json()[0]["id"]

    resp = await client.post(
        f"/census/tribes/{tribe_data['id']}/requests/{request_id}",
        json={"action": "approve"},
        headers=leader_headers,
    )
    assert resp.status_code == 200
    assert "approved" in resp.json()["detail"]

    # Verify member count increased
    members_resp = await client.get(
        f"/census/tribes/{tribe_data['id']}/members", headers=leader_headers
    )
    assert len(members_resp.json()) == 2


async def test_deny_join_request(client, tribe_with_leader, second_auth_headers):
    tribe_data, leader_headers = tribe_with_leader
    invite_code = tribe_data["invite_code"]
    await client.post(f"/census/tribes/join/{invite_code}", headers=second_auth_headers)

    requests_resp = await client.get(
        f"/census/tribes/{tribe_data['id']}/requests", headers=leader_headers
    )
    request_id = requests_resp.json()[0]["id"]

    resp = await client.post(
        f"/census/tribes/{tribe_data['id']}/requests/{request_id}",
        json={"action": "deny"},
        headers=leader_headers,
    )
    assert resp.status_code == 200
    assert "denied" in resp.json()["detail"].lower()


async def test_approve_already_processed_fails(
    client, tribe_with_leader, second_auth_headers
):
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
    resp = await client.post(
        f"/census/tribes/{tribe_data['id']}/requests/{request_id}",
        json={"action": "approve"},
        headers=leader_headers,
    )
    assert resp.status_code == 400
    assert "already processed" in resp.json()["detail"]
