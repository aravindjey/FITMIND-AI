import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cross_user_isolation(async_client: AsyncClient, test_user_a: dict, test_user_b: dict):
    headers_a = test_user_a["headers"]
    headers_b = test_user_b["headers"]

    # 1. User A creates profile
    profile_a = {
        "age": 30,
        "sex": "female",
        "height_cm": 165.0,
        "current_weight_kg": 60.0,
        "activity_level": "lightly_active",
        "goal": {"primary_goal": "fat_loss"}
    }
    res_a = await async_client.post("/api/v1/athlete/profile", json=profile_a, headers=headers_a)
    assert res_a.status_code == 201
    data_a = res_a.json()
    assert data_a["user_id"] == str(test_user_a["user"].id)

    # 2. User B fetches their own profile -> Should be 404 (User B hasn't created profile)
    res_b = await async_client.get("/api/v1/athlete/profile", headers=headers_b)
    assert res_b.status_code == 404
    assert "not found" in res_b.json()["detail"].lower()

    # 3. User B attempts to access User A's profile via User B's token -> Receives User B's state only (404)
    # The API endpoint /athlete/profile resolves user strictly from JWT token `sub` field.
    # User B cannot inject User A's ID into the query.
    res_b_verify = await async_client.get("/api/v1/athlete/profile", headers=headers_b)
    assert res_b_verify.status_code == 404
    assert res_b_verify.json() != data_a

    # 4. User B creates their own profile
    profile_b = {
        "age": 22,
        "sex": "male",
        "height_cm": 185.0,
        "current_weight_kg": 85.0,
        "activity_level": "very_active",
        "goal": {"primary_goal": "strength"}
    }
    res_b_create = await async_client.post("/api/v1/athlete/profile", json=profile_b, headers=headers_b)
    assert res_b_create.status_code == 201
    data_b = res_b_create.json()
    assert data_b["user_id"] == str(test_user_b["user"].id)
    assert data_b["user_id"] != data_a["user_id"]

    # 5. Verify User A gets User A's profile and User B gets User B's profile
    fetch_a = await async_client.get("/api/v1/athlete/profile", headers=headers_a)
    fetch_b = await async_client.get("/api/v1/athlete/profile", headers=headers_b)

    assert fetch_a.json()["current_weight_kg"] == 60.0
    assert fetch_b.json()["current_weight_kg"] == 85.0
    assert fetch_a.json()["user_id"] != fetch_b.json()["user_id"]
