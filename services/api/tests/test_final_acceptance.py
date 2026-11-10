import uuid
import pytest
from httpx import AsyncClient

from app.agents.base import AgentInputEnvelope
from app.agents.training_agent import TrainingAgent
from app.agents.nutrition_agent import NutritionAgent
from app.agents.orchestrator import CoachOrchestrator
from app.agents.stubs import (
    BodyAnalysisAgent,
    FitnessCoachingAgent,
    ProgressAgent,
    RecoveryAgent,
    SafetyValidationComponent,
    LifestyleHabitAgent,
)
from app.ai.factory import OpenAICompatibleProvider, GeminiProvider
from pydantic import BaseModel


class SampleSchema(BaseModel):
    summary: str = "fallback_summary"


@pytest.mark.asyncio
async def test_all_eight_agents_individually_and_orchestrator():
    uid = uuid.uuid4()
    sample_context = {
        "athlete_summary": {
            "age": 27,
            "sex": "male",
            "height_cm": 178.0,
            "weight_kg": 76.0,
            "training_experience_years": 2.5,
            "activity_level": "moderately_active",
            "primary_goal": "muscle_gain",
        },
        "constraints": {
            "equipment": ["barbell", "dumbbell", "bodyweight"],
            "days_per_week": 4,
            "preferred_days": ["Mon", "Tue", "Thu", "Fri"],
            "dietary_type": "vegetarian",
            "weekly_budget_inr": 3000.0,
            "meals_per_day": 4,
            "allergies": ["peanuts"],
        },
        "nutrition_targets": {
            "bmr_kcal": 1755,
            "tdee_kcal": 2720,
            "target_calories": 3020,
            "protein_grams": 152,
            "carbs_grams": 395,
            "fat_grams": 91,
        },
        "recent_weight_trend": {"ema_latest_kg": 76.0, "weekly_rate_kg": 0.22},
        "recent_recovery": {"readiness_score": 84, "status": "optimal", "intensity_modifier": 1.0},
        "personal_records": [{"exercise_name": "Barbell Bench Press", "estimated_1rm_kg": 100.0}],
        "recent_sessions": [{"workout_name": "Upper Body A"}],
        "latest_check_in": {"hydration_liters": 2.4, "sleep_hours": 6.5, "nutrition_adherence_percent": 75},
        "checkin_streak_days": 3,
    }

    # 1. BodyAnalysisAgent
    body_out = await BodyAnalysisAgent().process(
        AgentInputEnvelope(
            user_id=uid,
            action="analyze_body_photo",
            context_data={"image_bytes": b"fake_img", "photo_type": "front", "weight_kg": 76.0, "previous_weight_kg": 75.5},
        )
    )
    assert body_out.agent_name == "BodyAnalysisAgent"
    assert body_out.validation_passed is True
    assert "uncertainty_disclaimer" in body_out.result_data
    assert "+0.50 kg" in body_out.result_data["weight_comparison_note"]

    # 2. TrainingAgent
    train_out = await TrainingAgent().process(
        AgentInputEnvelope(user_id=uid, action="generate_workout", context_data=sample_context)
    )
    assert train_out.agent_name == "TrainingAgent"
    assert train_out.validation_passed is True
    assert len(train_out.result_data["days"]) == 4

    # 3. NutritionAgent
    nut_out = await NutritionAgent().process(
        AgentInputEnvelope(user_id=uid, action="generate_nutrition", context_data=sample_context)
    )
    assert nut_out.agent_name == "NutritionAgent"
    assert nut_out.validation_passed is True
    assert len(nut_out.result_data["meals"]) == 4

    # 4. FitnessCoachingAgent
    coach_out = await FitnessCoachingAgent().process(
        AgentInputEnvelope(
            user_id=uid,
            action="chat",
            context_data=sample_context,
            user_prompt="How much protein and calories should I eat on my vegetarian budget?",
        )
    )
    assert coach_out.agent_name == "FitnessCoachingAgent"
    assert "3020 kcal" in coach_out.result_data["answer"]
    assert len(coach_out.result_data["referenced_metrics"]) == 4

    # 5. ProgressAgent
    prog_out = await ProgressAgent().process(
        AgentInputEnvelope(user_id=uid, action="analyze_progress", context_data=sample_context)
    )
    assert prog_out.agent_name == "ProgressAgent"
    assert prog_out.result_data["trajectory_status"] == "on_track"

    # 6. RecoveryAgent
    rec_out = await RecoveryAgent().process(
        AgentInputEnvelope(
            user_id=uid,
            action="evaluate_recovery",
            context_data={"check_in_metrics": {"sleep_hours": 8.0, "sleep_quality_score": 8, "energy_score": 8, "soreness_score": 2, "stress_score": 3}},
        )
    )
    assert rec_out.agent_name == "RecoveryAgent"
    assert rec_out.result_data["readiness_score"] >= 80

    # 7. SafetyValidationComponent (valid + invalid checks)
    safe_out = await SafetyValidationComponent().process(
        AgentInputEnvelope(
            user_id=uid,
            action="validate_safety",
            context_data={
                "nutrition_plan": {"targets": {"target_calories": 900, "bmr_kcal": 1700, "tdee_kcal": 2500}, "meals": [{"name": "M1", "ingredients": [{"name": "Peanuts"}]}]},
                "allergies": ["peanuts"],
            },
        )
    )
    assert safe_out.agent_name == "SafetyValidationComponent"
    assert safe_out.validation_passed is False
    assert len(safe_out.result_data["violations"]) >= 2

    # 8. LifestyleHabitAgent
    hab_out = await LifestyleHabitAgent().process(
        AgentInputEnvelope(user_id=uid, action="evaluate_habits", context_data=sample_context)
    )
    assert hab_out.agent_name == "LifestyleHabitAgent"
    assert len(hab_out.result_data["habit_recommendations"]) >= 2

    # 9. CoachOrchestrator multi-spoke routing
    orch_out = await CoachOrchestrator().process(
        AgentInputEnvelope(
            user_id=uid,
            action="chat",
            context_data=sample_context,
            user_prompt="My weight trend is stalling and I feel sore after squat sets and low water hydration.",
        )
    )
    assert orch_out.agent_name == "CoachOrchestrator"
    for expected_spoke in ("FitnessCoachingAgent", "ProgressAgent", "RecoveryAgent", "LifestyleHabitAgent"):
        assert expected_spoke in orch_out.result_data["target_spokes"]


@pytest.mark.asyncio
async def test_provider_failure_graceful_fallback():
    # Verify OpenAICompatibleProvider & GeminiProvider gracefully fall back with is_fallback=True when unreachable/unauthenticated
    openai_prov = OpenAICompatibleProvider(
        api_key="invalid_key",
        model_name="gpt-4o-mini",
        vision_model_name="gpt-4o-mini",
        base_url="http://127.0.0.1:1",  # unreachable port
    )
    res_oai = await openai_prov.generate_structured_output("test", "sys", SampleSchema)
    assert res_oai.is_fallback is True
    assert res_oai.data.summary == "fallback_summary"

    gemini_prov = GeminiProvider(
        api_key="invalid_key",
        model_name="gemini-2.5-flash",
        vision_model_name="gemini-2.5-flash",
    )
    res_gem = await gemini_prov.generate_structured_output("test", "sys", SampleSchema)
    assert res_gem.is_fallback is True
    assert res_gem.data.summary == "fallback_summary"


@pytest.mark.asyncio
async def test_security_Persistence_and_error_handling(
    async_client: AsyncClient,
    test_user_a: dict,
    test_user_b: dict,
):
    headers_a = test_user_a["headers"]
    headers_b = test_user_b["headers"]

    # 1. Unauthorized access blocked
    unauth = await async_client.get("/api/v1/athlete/state")
    assert unauth.status_code == 401

    # 2. Onboarding User A
    await async_client.post(
        "/api/v1/athlete/onboarding",
        json={
            "age": 28,
            "sex": "male",
            "height_cm": 180.0,
            "current_weight_kg": 78.0,
            "activity_level": "moderately_active",
            "primary_goal": "strength",
            "training_experience_years": 3.0,
            "days_per_week": 4,
            "preferred_days": ["Mon", "Tue", "Thu", "Fri"],
            "session_duration_minutes": 60,
            "available_equipment": ["barbell", "dumbbell", "bodyweight"],
            "dietary_type": "omnivore",
            "weekly_food_budget_inr": 3200.0,
            "meals_per_day": 4,
            "staple_foods": ["Eggs", "Rice", "Chicken Breast"],
            "liked_foods": [],
            "disliked_foods": [],
            "allergies": [],
            "avoided_foods": [],
        },
        headers=headers_a,
    )

    # 3. Invalid photo_type rejected with 400
    bad_photo = await async_client.post(
        "/api/v1/progress/photos/analyze",
        json={"photo_type": "diagonal_invalid"},
        headers=headers_a,
    )
    assert bad_photo.status_code == 400

    # 4. Invalid base64 rejected with 400
    bad_b64 = await async_client.post(
        "/api/v1/progress/photos/analyze",
        json={"photo_type": "front", "image_base64": "!!!not_valid_base64$$$"},
        headers=headers_a,
    )
    assert bad_b64.status_code == 400

    # 5. Record body measurement, reminder, logout, re-login, and verify persistence
    meas_res = await async_client.post(
        "/api/v1/progress/measurements",
        json={"waist_cm": 81.5, "chest_cm": 104.0, "bicep_right_cm": 37.5},
        headers=headers_a,
    )
    assert meas_res.status_code == 201

    rem_res = await async_client.post(
        "/api/v1/progress/reminders",
        json={"title": "Creatine & Hydration", "notification_type": "hydration", "scheduled_time": "09:00"},
        headers=headers_a,
    )
    assert rem_res.status_code == 201
    rem_id = rem_res.json()["id"]

    # User B cannot delete User A's reminder
    del_by_b = await async_client.delete(f"/api/v1/progress/reminders/{rem_id}", headers=headers_b)
    assert del_by_b.status_code == 404

    # Logout User A and log back in
    logout_res = await async_client.post("/api/v1/auth/logout", headers=headers_a)
    assert logout_res.status_code == 200

    relogin_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "usera@example.com", "password": "Password123!"},
    )
    assert relogin_res.status_code == 200
    new_headers = {"Authorization": f"Bearer {relogin_res.json()['access_token']}"}

    # Verify records remain persisted after logout/login
    persisted_meas = await async_client.get("/api/v1/progress/measurements", headers=new_headers)
    assert any(m["waist_cm"] == 81.5 for m in persisted_meas.json())

    persisted_rems = await async_client.get("/api/v1/progress/reminders", headers=new_headers)
    assert any(r["id"] == rem_id for r in persisted_rems.json())
