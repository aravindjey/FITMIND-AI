import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_get_update_profile(async_client: AsyncClient, test_user_a: dict):
    headers = test_user_a["headers"]

    # 1. Profile initially not found
    get_res = await async_client.get("/api/v1/athlete/profile", headers=headers)
    assert get_res.status_code == 404

    # 2. Create Profile
    profile_data = {
        "age": 28,
        "sex": "male",
        "height_cm": 178.0,
        "current_weight_kg": 76.5,
        "timezone": "Asia/Kolkata",
        "training_experience_years": 3.5,
        "activity_level": "moderately_active",
        "occupation_type": "Software Engineer",
        "sport_name": "Cricket",
        "sport_position": "Batsman",
        "training_preferences": {"days_per_week": 4},
        "goal": {
            "primary_goal": "muscle_gain",
            "target_weight_kg": 80.0
        }
    }
    create_res = await async_client.post("/api/v1/athlete/profile", json=profile_data, headers=headers)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["age"] == 28
    assert created_data["height_cm"] == 178.0
    assert created_data["goals"][0]["primary_goal"] == "muscle_gain"

    # 3. Get Profile
    get_res2 = await async_client.get("/api/v1/athlete/profile", headers=headers)
    assert get_res2.status_code == 200
    assert get_res2.json()["current_weight_kg"] == 76.5

    # 4. Update Profile
    update_data = {
        "current_weight_kg": 77.2,
        "activity_level": "very_active"
    }
    update_res = await async_client.put("/api/v1/athlete/profile", json=update_data, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["current_weight_kg"] == 77.2
    assert update_res.json()["activity_level"] == "very_active"
