import pytest
from httpx import AsyncClient
from app.engines.nutrition_engine import calculate_bmr_mifflin_st_jeor, calculate_tdee, calculate_nutrition_targets
from app.engines.workout_engine import calculate_next_load_prescription, calculate_session_volume, calculate_recovery_readiness
from app.engines.safety_engine import validate_nutrition_plan_safety, validate_workout_plan_safety


def test_deterministic_nutrition_engine():
    # 25yo male, 75kg, 178cm -> BMR = 10*75 + 6.25*178 - 5*25 + 5 = 750 + 1112.5 - 125 + 5 = 1742 kcal
    bmr = calculate_bmr_mifflin_st_jeor(75.0, 178.0, 25, "male")
    assert bmr == 1742

    tdee = calculate_tdee(bmr, "moderately_active")
    assert tdee == int(round(1742 * 1.55))

    targets = calculate_nutrition_targets(
        weight_kg=75.0,
        height_cm=178.0,
        age=25,
        sex="male",
        activity_level="moderately_active",
        primary_goal="muscle_gain",
        dietary_type="vegetarian",
    )
    assert targets["bmr_kcal"] == 1742
    assert targets["protein_grams"] == 150
    assert targets["target_calories"] > tdee


def test_deterministic_workout_and_safety_engines():
    # Progressive overload increase
    presc_up = calculate_next_load_prescription(100.0, 10, 6, 10, actual_rpe=7.5, target_rpe=8.0)
    assert presc_up["action"] == "increase"
    assert presc_up["recommended_weight_kg"] == 102.5

    # RPE overshoot deload
    presc_down = calculate_next_load_prescription(100.0, 5, 6, 10, actual_rpe=10.0, target_rpe=8.0)
    assert presc_down["action"] == "deload"
    assert presc_down["recommended_weight_kg"] < 100.0

    # Recovery readiness
    rec = calculate_recovery_readiness(8.0, 8, 8, 2, 3)
    assert rec["readiness_score"] >= 80
    assert rec["status"] == "optimal"

    # Safety check catches allergen & sub-floor calories
    unsafe_nut = validate_nutrition_plan_safety(
        target_calories=950,
        bmr_kcal=1650,
        tdee_kcal=2400,
        allergies=["peanuts"],
        meals=[{"name": "Snack", "ingredients": [{"name": "Roasted Peanuts"}]}],
    )
    assert unsafe_nut["is_valid"] is False
    assert len(unsafe_nut["violations"]) >= 2


@pytest.mark.asyncio
async def test_complete_user_journey_and_isolation(
    async_client: AsyncClient,
    test_user_a: dict,
    test_user_b: dict,
):
    headers_a = test_user_a["headers"]
    headers_b = test_user_b["headers"]

    # 1. Complete Onboarding for User A (Indian Vegetarian context with INR budget & peanut allergy)
    onboarding_payload = {
        "age": 26,
        "sex": "male",
        "height_cm": 176.0,
        "current_weight_kg": 74.0,
        "timezone": "Asia/Kolkata",
        "occupation_type": "Software Engineer",
        "activity_level": "moderately_active",
        "primary_goal": "muscle_gain",
        "target_weight_kg": 78.0,
        "training_experience_years": 2.0,
        "days_per_week": 4,
        "preferred_days": ["Mon", "Tue", "Thu", "Fri"],
        "session_duration_minutes": 60,
        "available_equipment": ["barbell", "dumbbell", "bodyweight"],
        "dietary_type": "vegetarian",
        "weekly_food_budget_inr": 2800.0,
        "currency_code": "INR",
        "meals_per_day": 4,
        "staple_foods": ["Paneer", "Moong Dal", "Roti", "Rice"],
        "liked_foods": ["Dahi", "Oats"],
        "disliked_foods": ["Mushrooms"],
        "allergies": ["peanuts"],
        "avoided_foods": [],
    }
    onb_res = await async_client.post("/api/v1/athlete/onboarding", json=onboarding_payload, headers=headers_a)
    assert onb_res.status_code == 201
    onb_data = onb_res.json()
    assert onb_data["hydrated_state"]["has_profile"] is True
    assert onb_data["hydrated_state"]["constraints"]["weekly_budget_inr"] == 2800.0
    assert "peanuts" in onb_data["hydrated_state"]["constraints"]["allergies"]

    # 2. Generate Workout Plan for User A
    wp_res = await async_client.post("/api/v1/training/generate-plan", headers=headers_a)
    assert wp_res.status_code == 201
    wp_data = wp_res.json()
    assert wp_data["has_active_plan"] is True
    assert len(wp_data["plan"]["days"]) == 4

    # 3. Log Workout Session & Achieve Personal Record
    session_payload = {
        "workout_name": "Upper Body A",
        "session_rpe": 8.0,
        "user_notes": "Felt strong on bench press",
        "sets": [
            {
                "exercise_name": "Barbell Bench Press",
                "set_number": 1,
                "weight_kg": 80.0,
                "reps_completed": 8,
                "actual_rpe": 8.0,
                "is_warmup": False,
            },
            {
                "exercise_name": "Barbell Bent-Over Row",
                "set_number": 2,
                "weight_kg": 70.0,
                "reps_completed": 10,
                "actual_rpe": 7.5,
                "is_warmup": False,
            },
        ],
    }
    log_ws_res = await async_client.post("/api/v1/training/sessions", json=session_payload, headers=headers_a)
    assert log_ws_res.status_code == 201
    ws_out = log_ws_res.json()
    assert ws_out["total_volume_kg"] == (80.0 * 8) + (70.0 * 10)
    assert len(ws_out["new_personal_records"]) == 2

    # 4. Generate Nutrition Plan for User A (Verify Peanut Allergy Excluded)
    np_res = await async_client.post("/api/v1/nutrition/generate-plan", headers=headers_a)
    assert np_res.status_code == 201
    np_data = np_res.json()
    assert np_data["has_active_plan"] is True
    assert np_data["plan"]["currency_code"] == "INR"
    for meal in np_data["plan"]["meals"]:
        for ing in meal["ingredients"]:
            assert "peanut" not in ing["name"].lower()

    # 5. Log Food Intake from Validated Database
    food_log_res = await async_client.post(
        "/api/v1/nutrition/logs",
        json={
            "food_name": "Low-Fat Paneer",
            "meal_type": "lunch",
            "preparation_state": "raw",
            "quantity_grams": 150.0,
        },
        headers=headers_a,
    )
    assert food_log_res.status_code == 201
    f_log = food_log_res.json()
    assert f_log["protein_g"] == 30.0  # 20g/100g * 1.5 = 30g

    daily_logs_res = await async_client.get("/api/v1/nutrition/logs", headers=headers_a)
    assert daily_logs_res.status_code == 200
    assert daily_logs_res.json()["totals"]["protein_g"] == 30.0

    # 6. Submit Daily Check-In & Verify Weight History Preservation
    ci_res = await async_client.post(
        "/api/v1/progress/check-ins",
        json={
            "weight_kg": 74.6,
            "energy_score": 8,
            "sleep_hours": 8.0,
            "sleep_quality_score": 8,
            "stress_score": 3,
            "soreness_score": 2,
            "hydration_liters": 3.5,
            "nutrition_adherence_percent": 95,
            "workout_completed": True,
        },
        headers=headers_a,
    )
    assert ci_res.status_code == 201
    ci_data = ci_res.json()
    assert ci_data["recovery_assessment"]["readiness_score"] >= 80

    # Check historical weight entries (initial 74.0 kg + check-in 74.6 kg)
    wh_res = await async_client.get("/api/v1/athlete/weight-history", headers=headers_a)
    assert wh_res.status_code == 200
    assert len(wh_res.json()["entries"]) >= 2

    # 7. Ask AI Coach Orchestrator a question
    chat_res = await async_client.post(
        "/api/v1/coach/chat",
        json={"message": "How should I progress my bench press and hit my protein goal?"},
        headers=headers_a,
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["validation_passed"] is True
    assert len(chat_data["target_spokes"]) >= 1

    # 8. Analyze Progress Photo with Explicit Uncertainty
    photo_res = await async_client.post(
        "/api/v1/progress/photos/analyze",
        json={"photo_type": "front", "weight_at_capture_kg": 74.6},
        headers=headers_a,
    )
    assert photo_res.status_code == 201
    photo_data = photo_res.json()
    assert "uncertainty_disclaimer" in photo_data["analysis"]
    assert "not a clinical or medical dexa" in photo_data["analysis"]["uncertainty_disclaimer"].lower()

    # 9. Create & Retrieve Reminder
    rem_res = await async_client.post(
        "/api/v1/progress/reminders",
        json={
            "title": "Evening Training Session",
            "notification_type": "workout",
            "scheduled_time": "18:00",
        },
        headers=headers_a,
    )
    assert rem_res.status_code == 201

    # 10. Verify Strict Multi-Tenant User Isolation (User B sees NONE of User A's records)
    b_wp = await async_client.get("/api/v1/training/active-plan", headers=headers_b)
    assert b_wp.json()["has_active_plan"] is False

    b_np = await async_client.get("/api/v1/nutrition/active-plan", headers=headers_b)
    assert b_np.json()["has_active_plan"] is False

    b_prs = await async_client.get("/api/v1/training/prs", headers=headers_b)
    assert b_prs.json() == []

    b_photos = await async_client.get("/api/v1/progress/photos", headers=headers_b)
    assert b_photos.json() == []

    b_rems = await async_client.get("/api/v1/progress/reminders", headers=headers_b)
    assert b_rems.json() == []
