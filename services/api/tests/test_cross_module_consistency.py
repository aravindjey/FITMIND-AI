import pytest
from httpx import AsyncClient
from app.engines.nutrition_engine import calculate_nutrition_targets, detect_goal_weight_conflict
from app.agents.nutrition_agent import FOOD_CATALOG_BY_NAME


def test_goal_target_weight_consistency_calculations():
    """Tasks A, B, C, D: Validate goal-specific calorie adjustments and conflict detection."""
    # Case 1: User-reported contradiction -> 83 kg, muscle_gain, target 76 kg, very_active
    # Previously produced TDEE 3210 kcal and a contradictory +12% surplus (3596 kcal).
    conflict_targets = calculate_nutrition_targets(
        weight_kg=83.0,
        height_cm=185.0,
        age=26,
        sex="male",
        activity_level="very_active",
        primary_goal="muscle_gain",
        dietary_type="omnivore",
        target_weight_kg=76.0,
    )
    assert round(conflict_targets["tdee_kcal"]) == 3210
    assert conflict_targets["goal_weight_conflict"] is True
    assert conflict_targets["effective_regime"] == "recomposition_cut"
    assert conflict_targets["calorie_adjustment_percent"] == -15.0
    assert conflict_targets["target_calories"] < conflict_targets["tdee_kcal"]
    assert conflict_targets["goal_conflict_warning"] is not None
    assert "83.0 kg" in conflict_targets["goal_conflict_warning"]
    assert "76.0 kg" in conflict_targets["goal_conflict_warning"]

    # Case 2: Valid muscle_gain -> 83 kg, muscle_gain, target 88 kg -> +12% surplus
    surplus_targets = calculate_nutrition_targets(
        weight_kg=83.0,
        height_cm=185.0,
        age=26,
        sex="male",
        activity_level="very_active",
        primary_goal="muscle_gain",
        dietary_type="omnivore",
        target_weight_kg=88.0,
    )
    assert surplus_targets["goal_weight_conflict"] is False
    assert surplus_targets["goal_conflict_warning"] is None
    assert surplus_targets["calorie_adjustment_percent"] == 12.0
    assert round(surplus_targets["target_calories"]) == 3596

    # Case 3: Valid fat_loss -> 83 kg, fat_loss, target 76 kg -> -20% deficit
    deficit_targets = calculate_nutrition_targets(
        weight_kg=83.0,
        height_cm=185.0,
        age=26,
        sex="male",
        activity_level="very_active",
        primary_goal="fat_loss",
        dietary_type="omnivore",
        target_weight_kg=76.0,
    )
    assert deficit_targets["goal_weight_conflict"] is False
    assert deficit_targets["calorie_adjustment_percent"] == -20.0
    assert deficit_targets["target_calories"] < deficit_targets["tdee_kcal"]

    # Case 4: Contradictory fat_loss -> 70 kg, fat_loss, target 78 kg
    fat_loss_conflict = detect_goal_weight_conflict(
        current_weight_kg=70.0,
        target_weight_kg=78.0,
        primary_goal="fat_loss",
    )
    assert fat_loss_conflict["has_conflict"] is True
    assert "fat loss" in fat_loss_conflict["warning"].lower()


@pytest.mark.asyncio
async def test_cross_module_consistency_end_to_end(
    async_client: AsyncClient,
    test_user_a: dict,
):
    """Tasks E, F, G, H, I: End-to-end verification of budget enforcement, food DB macro math,
    and AI Coach grounding when active_workout_plan is None vs present.
    """
    headers = test_user_a["headers"]

    # 1. Complete onboarding with 83 kg, muscle_gain, target 76 kg, weekly budget ₹2500 INR
    onboard_res = await async_client.post(
        "/api/v1/athlete/onboarding",
        headers=headers,
        json={
            "age": 26,
            "sex": "male",
            "height_cm": 185.0,
            "current_weight_kg": 83.0,
            "training_experience_years": 2.0,
            "activity_level": "very_active",
            "primary_goal": "muscle_gain",
            "target_weight_kg": 76.0,
            "days_per_week": 4,
            "preferred_days": ["Mon", "Tue", "Thu", "Fri"],
            "session_duration_minutes": 60,
            "available_equipment": ["barbell", "dumbbells", "bench", "cables", "pullup_bar"],
            "dietary_type": "omnivore",
            "weekly_food_budget_inr": 2500.0,
            "meals_per_day": 4,
            "staple_foods": ["Cooked White Basmati Rice", "Whole Wheat Roti / Chapati (Cooked)", "Chicken Breast (Cooked)"],
            "liked_foods": ["Whole Boiled Eggs", "Low-Fat Curd / Dahi"],
            "disliked_foods": [],
            "allergies": [],
            "avoided_foods": [],
        },
    )
    assert onboard_res.status_code == 201
    state = onboard_res.json()["hydrated_state"]

    # Verify conflict detection in hydrated state and nutrition targets endpoint
    assert state["nutrition_targets"]["goal_weight_conflict"] is True
    assert state["nutrition_targets"]["target_calories"] < state["nutrition_targets"]["tdee_kcal"]
    assert state["active_workout_plan"] is None

    targets_res = await async_client.get("/api/v1/nutrition/targets", headers=headers)
    assert targets_res.status_code == 200
    t_json = targets_res.json()
    assert t_json["goal_weight_conflict"] is True
    assert t_json["calorie_adjustment_percent"] == -15.0

    # 2. Task G & H: Verify AI Coach does NOT claim an active 4-day split exists when active_workout_plan is None
    coach_res_no_plan = await async_client.post(
        "/api/v1/coach/chat",
        headers=headers,
        json={"message": "How should I structure my training and nutrition right now?"},
    )
    assert coach_res_no_plan.status_code == 200
    coach_data = coach_res_no_plan.json()
    assert "no active workout plan generated yet" in coach_data["answer"].lower()
    assert "within your 4-day split" not in coach_data["answer"].lower()
    assert any("Active Workout Plan: None" in m for m in coach_data["referenced_metrics"])
    assert "83.0 kg" in coach_data["answer"] and "76.0 kg" in coach_data["answer"]

    # 3. Task E & F: Generate meal plan and verify strict ₹2500/week budget & exact food DB math
    nut_plan_res = await async_client.post("/api/v1/nutrition/generate-plan", headers=headers)
    assert nut_plan_res.status_code == 201
    plan = nut_plan_res.json()["plan"]

    weekly_cost = round(plan["estimated_daily_cost_inr"] * 7.0, 2)
    assert weekly_cost <= 2500.0, f"Weekly cost ₹{weekly_cost} exceeded budget ₹2500"
    total_meal_kcal = sum(int(m["target_calories"]) for m in plan["meals"])
    total_meal_pro = round(sum(float(m["protein_g"]) for m in plan["meals"]), 1)
    total_meal_carb = round(sum(float(m["carbs_g"]) for m in plan["meals"]), 1)
    total_meal_fat = round(sum(float(m["fat_g"]) for m in plan["meals"]), 1)

    assert abs(total_meal_kcal - int(plan["daily_calories"])) <= 5, (
        f"Meal calorie sum ({total_meal_kcal} kcal) did not reconcile with daily target ({plan['daily_calories']} kcal)"
    )
    assert abs(total_meal_pro - float(plan["protein_grams"])) <= 3.0, (
        f"Meal protein sum ({total_meal_pro}g) deviated from target ({plan['protein_grams']}g)"
    )
    assert total_meal_pro >= float(plan["protein_grams"]) - 1.0, (
        f"Meal protein sum ({total_meal_pro}g) fell below minimum requirement ({plan['protein_grams']}g)"
    )
    assert abs(total_meal_carb - float(plan["carbs_grams"])) <= 15.0, (
        f"Meal carbs sum ({total_meal_carb}g) deviated from target ({plan['carbs_grams']}g)"
    )
    assert abs(total_meal_fat - float(plan["fat_grams"])) <= 8.0, (
        f"Meal fat sum ({total_meal_fat}g) deviated from target ({plan['fat_grams']}g)"
    )

    # Also test with an explicit high-surplus target (target_weight_kg=90 kg -> 3596 kcal) under ₹2500/wk budget
    upd_res = await async_client.put(
        "/api/v1/athlete/profile",
        headers=headers,
        json={
            "current_weight_kg": 83.0,
            "goal": {"primary_goal": "muscle_gain", "target_weight_kg": 90.0},
        },
    )
    assert upd_res.status_code == 200

    nut_plan_surplus_res = await async_client.post("/api/v1/nutrition/generate-plan", headers=headers)
    assert nut_plan_surplus_res.status_code == 201
    surplus_plan = nut_plan_surplus_res.json()["plan"]
    surplus_weekly_cost = round(surplus_plan["estimated_daily_cost_inr"] * 7.0, 2)
    assert surplus_weekly_cost <= 2500.0, f"Surplus weekly cost ₹{surplus_weekly_cost} exceeded ₹2500"

    # Verify every meal's ingredients match the underlying food database per-100g macros
    for meal in surplus_plan["meals"]:
        ing_kcal_sum = 0.0
        ing_pro_sum = 0.0
        for ing in meal["ingredients"]:
            db_item = FOOD_CATALOG_BY_NAME.get(ing["name"])
            assert db_item is not None, f"Ingredient {ing['name']} missing from DEFAULT_FOOD_ITEMS"
            qty = ing["quantity_grams"]
            expected_kcal = int(round((db_item["calories_per_100g"] * qty) / 100.0))
            expected_pro = round((db_item["protein_per_100g"] * qty) / 100.0, 1)
            assert abs(ing["calories"] - expected_kcal) <= 1
            assert abs(ing["protein_g"] - expected_pro) <= 0.2
            ing_kcal_sum += ing["calories"]
            ing_pro_sum += ing["protein_g"]
        assert abs(meal["target_calories"] - round(ing_kcal_sum, 1)) <= 1.0
        assert abs(meal["protein_g"] - round(ing_pro_sum, 1)) <= 0.5

    # 4. Generate an active workout plan and verify AI Coach now references the active plan record
    wp_res = await async_client.post("/api/v1/training/generate-plan", headers=headers)
    assert wp_res.status_code == 201
    wp_name = wp_res.json()["plan"]["name"]

    coach_res_with_plan = await async_client.post(
        "/api/v1/coach/chat",
        headers=headers,
        json={"message": "What is my active training split now?"},
    )
    assert coach_res_with_plan.status_code == 200
    coach_data_after = coach_res_with_plan.json()
    assert wp_name in coach_data_after["answer"]
    assert any(f"Active Workout Plan: {wp_name}" in m for m in coach_data_after["referenced_metrics"])
