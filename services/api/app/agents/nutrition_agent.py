from typing import Dict, Any, List
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentInputEnvelope, AgentOutputEnvelope
from app.ai.factory import get_llm_provider
from app.engines.nutrition_engine import calculate_nutrition_targets
from app.engines.safety_engine import validate_nutrition_plan_safety
from app.services.seed_data import DEFAULT_FOOD_ITEMS


FOOD_CATALOG_BY_NAME: Dict[str, Dict[str, Any]] = {
    item["name"]: item for item in DEFAULT_FOOD_ITEMS
}


def compute_ingredient_from_db(food_name: str, quantity_grams: float) -> Dict[str, Any]:
    """Computes exact ingredient calories, macros, and INR cost strictly from the validated
    DEFAULT_FOOD_ITEMS per-100g catalog.
    """
    item = FOOD_CATALOG_BY_NAME[food_name]
    grams = max(5.0, round(float(quantity_grams), 0))
    mult = grams / 100.0
    return {
        "name": item["name"],
        "quantity_grams": grams,
        "preparation_state": item["preparation_state"],
        "calories": int(round(item["calories_per_100g"] * mult)),
        "protein_g": round(item["protein_per_100g"] * mult, 1),
        "carbs_g": round(item["carbs_per_100g"] * mult, 1),
        "fat_g": round(item["fat_per_100g"] * mult, 1),
        "cost_inr": round(item["estimated_cost_inr_per_100g"] * mult, 2),
    }


class MealIngredientSchema(BaseModel):
    name: str = "Whole Wheat Roti / Chapati (Cooked)"
    quantity_grams: float = 100.0
    preparation_state: str = "cooked"
    calories: int = 297
    protein_g: float = 9.6
    carbs_g: float = 58.0
    fat_g: float = 3.0
    cost_inr: float = 8.0


class PlannedMealSchema(BaseModel):
    meal_number: int = 1
    name: str = "Meal 1 - Breakfast"
    time_of_day: str = "08:00 AM"
    target_calories: int = 500
    protein_g: int = 35
    carbs_g: int = 55
    fat_g: int = 15
    estimated_cost_inr: float = 55.0
    recipe_instructions: str = "Prepare with minimal cooking oil and serve warm."
    ingredients: List[MealIngredientSchema] = Field(default_factory=list)


class NutritionPlanLLMOutput(BaseModel):
    plan_name: str = "Personalized Indian & Balanced Nutrition Plan"
    explanation: str = "Calculated from Mifflin-St Jeor BMR/TDEE and tailored to INR budget and dietary restrictions."
    meals: List[PlannedMealSchema] = Field(default_factory=list)


class NutritionAgent(BaseAgent):
    """Component #3: Nutrition Agent.
    Uses deterministic BMR/TDEE/Macro calculations and validated food items to construct
    allergen-safe, INR-budget-enforced meal plans.
    """

    @property
    def agent_name(self) -> str:
        return "NutritionAgent"

    def _build_deterministic_meals(self, context: Dict[str, Any], targets: Dict[str, Any]) -> Dict[str, Any]:
        constraints = context.get("constraints") or {}
        dietary_type = str(constraints.get("dietary_type", "omnivore")).lower()
        meals_per_day = int(constraints.get("meals_per_day", 4))
        allergies = [a.lower().strip() for a in constraints.get("allergies", [])]
        weekly_budget_inr = float(constraints.get("weekly_budget_inr") or 2500.0)
        daily_budget_inr = round(weekly_budget_inr / 7.0, 2)

        total_kcal = int(targets["target_calories"])
        total_pro = int(targets["protein_grams"])
        total_carb = int(targets["carbs_grams"])
        total_fat = int(targets["fat_grams"])

        is_veg = dietary_type in ("vegetarian", "vegan", "jain")
        is_vegan = dietary_type == "vegan"
        has_dairy_allergy = any(x in allergies for x in ("dairy", "milk", "lactose", "paneer", "whey", "curd"))
        has_peanut_allergy = any(x in allergies for x in ("peanut", "peanuts", "nuts", "nut"))
        has_egg_allergy = any(x in allergies for x in ("egg", "eggs"))
        has_soy_allergy = any(x in allergies for x in ("soy", "soya"))

        # Select validated catalog food names + baseline grams per meal
        # Use cost-aware protein selection so weekly cost fits within weekly_budget_inr
        high_budget = daily_budget_inr >= 380.0

        if is_vegan or has_dairy_allergy:
            pro_breakfast = ("Soya Chunks (Raw / Dry Weight)", 55.0) if not has_soy_allergy else ("Moong / Toor Dal Tadka (Cooked)", 220.0)
            pro_lunch = ("Rajma / Chana Masala (Cooked)", 250.0)
            pro_snack = ("Soya Chunks (Raw / Dry Weight)", 45.0) if not has_soy_allergy else ("Rajma / Chana Masala (Cooked)", 200.0)
            pro_dinner = ("Moong / Toor Dal Tadka (Cooked)", 250.0)
        elif is_veg:
            pro_breakfast = (
                ("Whey Protein Isolate / Concentrate", 30.0)
                if high_budget
                else ("Soya Chunks (Raw / Dry Weight)", 50.0) if not has_soy_allergy else ("Low-Fat Paneer / Cottage Cheese (Raw)", 90.0)
            )
            pro_lunch = ("Low-Fat Paneer / Cottage Cheese (Raw)", 100.0) if daily_budget_inr >= 240.0 else ("Rajma / Chana Masala (Cooked)", 240.0)
            pro_snack = ("Soya Chunks (Raw / Dry Weight)", 50.0) if not has_soy_allergy else ("Dahi / Toned Milk Curd", 200.0)
            pro_dinner = ("Moong / Toor Dal Tadka (Cooked)", 240.0)
        else:
            pro_breakfast = ("Whole Boiled Eggs", 150.0) if not has_egg_allergy else ("Low-Fat Paneer / Cottage Cheese (Raw)", 100.0)
            pro_lunch = ("Chicken Breast (Grilled / Cooked)", 140.0) if daily_budget_inr >= 260.0 else ("Whole Boiled Eggs", 150.0)
            pro_snack = (
                ("Whey Protein Isolate / Concentrate", 30.0)
                if high_budget and not has_dairy_allergy
                else ("Soya Chunks (Raw / Dry Weight)", 50.0) if not has_soy_allergy else ("Whole Boiled Eggs", 120.0)
            )
            pro_dinner = (
                ("Rohu / Indian Seer Fish Curry (Cooked)", 140.0)
                if high_budget
                else ("Chicken Breast (Grilled / Cooked)", 130.0) if daily_budget_inr >= 280.0 else ("Moong / Toor Dal Tadka (Cooked)", 240.0)
            )

        fat_snack_item = (
            ("Dahi / Toned Milk Curd", 150.0)
            if has_peanut_allergy and not (is_vegan or has_dairy_allergy)
            else ("Ripe Banana", 100.0)
            if has_peanut_allergy
            else ("Roasted Peanuts / Natural Peanut Butter", 25.0)
        )

        meal_templates = [
            ("Meal 1: High-Protein Indian Breakfast", "08:00 AM", pro_breakfast, ("Rolled Oats (Raw)", 65.0), fat_snack_item),
            ("Meal 2: Balanced Indian Thali Lunch", "01:30 PM", pro_lunch, ("Steamed Basmati Rice (Cooked)", 220.0), ("Mixed Seasonal Sabzi (Palak, Gobhi, Beans)", 150.0)),
            ("Meal 3: Pre/Post-Workout Fuel Snack", "05:30 PM", pro_snack, ("Ripe Banana", 120.0), fat_snack_item),
            ("Meal 4: Recovery Dinner", "09:00 PM", pro_dinner, ("Whole Wheat Roti / Chapati (Cooked)", 110.0), ("Mixed Seasonal Sabzi (Palak, Gobhi, Beans)", 150.0)),
        ]

        selected_templates = meal_templates[:max(1, min(4, meals_per_day))]
        scale_factor = max(0.65, min(1.50, total_kcal / 2200.0))

        # Construct initial ingredient quantities per meal (coupled solver will reconcile exact macros)
        raw_meal_specs = []
        for idx, (m_title, m_time, pro_spec, carb_spec, side_spec) in enumerate(selected_templates, start=1):
            raw_meal_specs.append({
                "idx": idx,
                "title": m_title,
                "time": m_time,
                "items": [
                    [pro_spec[0], round(pro_spec[1], 0)],
                    [carb_spec[0], round(carb_spec[1] * scale_factor, 0)],
                    [side_spec[0], round(side_spec[1], 0)],
                ],
            })

        def _evaluate_plan_totals(specs: List[Dict[str, Any]]) -> Dict[str, float]:
            cal = 0
            pro = 0.0
            carb = 0.0
            fat = 0.0
            cost = 0.0
            for sp in specs:
                for f_name, f_grams in sp["items"]:
                    ing = compute_ingredient_from_db(f_name, f_grams)
                    cal += int(ing["calories"])
                    pro += float(ing["protein_g"])
                    carb += float(ing["carbs_g"])
                    fat += float(ing["fat_g"])
                    cost += float(ing["cost_inr"])
            return {
                "calories": cal,
                "protein_g": round(pro, 1),
                "carbs_g": round(carb, 1),
                "fat_g": round(fat, 1),
                "cost_inr": round(cost, 2),
            }

        def _serving_bounds(food_name: str, slot_idx: int) -> tuple[float, float]:
            """Returns realistic culinary gram bounds (min_g, max_g) for each food item and meal slot."""
            item = FOOD_CATALOG_BY_NAME[food_name]
            cat = item["category"]
            prep = item["preparation_state"]
            if cat == "supplement":
                return (20.0, 60.0)
            if "Soya Chunks" in food_name:
                return (25.0, 80.0)
            if cat == "nut_seed":
                return (10.0, 55.0)
            if slot_idx == 0:
                # Primary protein source (cooked eggs, chicken, fish, raw paneer, cooked dal/rajma)
                return (50.0, 260.0) if prep == "raw" else (80.0, 320.0)
            if slot_idx == 1:
                # Primary carbohydrate staple (raw oats, cooked rice/roti, banana)
                return (30.0, 140.0) if prep == "raw" else (60.0, 420.0)
            return (50.0, 220.0)

        # Coupled Macro, Calorie & INR Budget Reconciliation Solver:
        # Accounts for secondary protein in grains/nuts/vegetables and secondary fat/carbs in protein sources.
        for _iter in range(6):
            # Step 1: Enforce weekly INR budget before and during macro adjustments
            totals = _evaluate_plan_totals(raw_meal_specs)
            if totals["cost_inr"] * 7.0 > weekly_budget_inr:
                budget_protein_fallback = (
                    "Soya Chunks (Raw / Dry Weight)"
                    if not has_soy_allergy
                    else ("Moong / Toor Dal Tadka (Cooked)" if is_veg else "Whole Boiled Eggs")
                )
                for sp in raw_meal_specs:
                    primary_name = sp["items"][0][0]
                    if primary_name in (
                        "Whey Protein Isolate / Concentrate",
                        "Low-Fat Paneer / Cottage Cheese (Raw)",
                        "Rohu / Indian Seer Fish Curry (Cooked)",
                        "Chicken Breast (Grilled / Cooked)",
                    ):
                        if _evaluate_plan_totals(raw_meal_specs)["cost_inr"] * 7.0 > weekly_budget_inr:
                            sp["items"][0][0] = budget_protein_fallback
                            sp["items"][0][1] = 50.0 if "Soya" in budget_protein_fallback else 160.0

            # Step 2: Reconcile Essential Fats via nut/seed or dairy side items (slot 2)
            totals = _evaluate_plan_totals(raw_meal_specs)
            fat_diff = float(total_fat) - totals["fat_g"]
            fat_Adjustable_specs = [
                sp for sp in raw_meal_specs
                if FOOD_CATALOG_BY_NAME[sp["items"][2][0]]["category"] in ("nut_seed", "dairy_paneer")
            ]
            if abs(fat_diff) > 1.5 and fat_Adjustable_specs:
                per_slot_fat_delta = fat_diff / float(len(fat_Adjustable_specs))
                for sp in fat_Adjustable_specs:
                    s_name, s_grams = sp["items"][2]
                    s_item = FOOD_CATALOG_BY_NAME[s_name]
                    fat_per_g = s_item["fat_per_100g"] / 100.0
                    if fat_per_g > 0:
                        min_g, max_g = _serving_bounds(s_name, 2)
                        new_g = max(min_g, min(max_g, round(s_grams + (per_slot_fat_delta / fat_per_g), 0)))
                        sp["items"][2][1] = new_g

            # Step 3: Reconcile Total Protein (Primary + Secondary from Carbs/Sides) to match total_pro
            totals = _evaluate_plan_totals(raw_meal_specs)
            pro_diff = float(total_pro) - totals["protein_g"]
            if abs(pro_diff) > 0.8:
                per_meal_pro_delta = pro_diff / float(len(raw_meal_specs))
                for sp in raw_meal_specs:
                    p_name, p_grams = sp["items"][0]
                    p_item = FOOD_CATALOG_BY_NAME[p_name]
                    pro_per_g = p_item["protein_per_100g"] / 100.0
                    cost_per_g = p_item["estimated_cost_inr_per_100g"] / 100.0
                    if pro_per_g <= 0:
                        continue
                    min_g, max_g = _serving_bounds(p_name, 0)
                    desired_g = round(p_grams + (per_meal_pro_delta / pro_per_g), 0)
                    new_g = max(min_g, min(max_g, desired_g))
                    if new_g > p_grams:
                        rem_budget = max(0.0, daily_budget_inr - _evaluate_plan_totals(raw_meal_specs)["cost_inr"])
                        added_cost = (new_g - p_grams) * cost_per_g
                        if added_cost > rem_budget and cost_per_g > 0:
                            new_g = p_grams + max(0.0, round((rem_budget * 0.95) / cost_per_g, 0))
                    sp["items"][0][1] = new_g

            # Step 4: Reconcile Total Calories & Carbohydrates via carbohydrate staples (slot 1)
            totals = _evaluate_plan_totals(raw_meal_specs)
            cal_diff = total_kcal - totals["calories"]
            if abs(cal_diff) > 2:
                per_meal_cal_delta = cal_diff / float(len(raw_meal_specs))
                for sp in raw_meal_specs:
                    c_name, c_grams = sp["items"][1]
                    c_item = FOOD_CATALOG_BY_NAME[c_name]
                    kcal_per_g = c_item["calories_per_100g"] / 100.0
                    cost_per_g = c_item["estimated_cost_inr_per_100g"] / 100.0
                    if kcal_per_g <= 0:
                        continue
                    min_g, max_g = _serving_bounds(c_name, 1)
                    desired_g = round(c_grams + (per_meal_cal_delta / kcal_per_g), 0)
                    new_g = max(min_g, min(max_g, desired_g))
                    if new_g > c_grams:
                        rem_budget = max(0.0, daily_budget_inr - _evaluate_plan_totals(raw_meal_specs)["cost_inr"])
                        added_cost = (new_g - c_grams) * cost_per_g
                        if added_cost > rem_budget and cost_per_g > 0:
                            new_g = c_grams + max(0.0, round((rem_budget * 0.98) / cost_per_g, 0))
                    sp["items"][1][1] = new_g

        # Final proportional budget guard if still above daily_budget_inr
        current_daily_cost = _evaluate_plan_totals(raw_meal_specs)["cost_inr"]
        if current_daily_cost > daily_budget_inr and current_daily_cost > 0:
            budget_ratio = (daily_budget_inr * 0.96) / current_daily_cost
            for sp in raw_meal_specs:
                for item_pair in sp["items"]:
                    item_pair[1] = max(15.0, round(item_pair[1] * budget_ratio, 0))

        # Final 1-gram polish on Lunch Rice (slot 1) and Lunch Protein (slot 0) to eliminate integer-gram rounding drift
        if len(raw_meal_specs) >= 2:
            # Fine-tune protein on Meal 2 primary protein
            pro_res = float(total_pro) - _evaluate_plan_totals(raw_meal_specs)["protein_g"]
            if abs(pro_res) >= 0.5:
                p_sp = raw_meal_specs[1]
                p_name, p_grams = p_sp["items"][0]
                p_item = FOOD_CATALOG_BY_NAME[p_name]
                pro_per_g = p_item["protein_per_100g"] / 100.0
                cost_per_g = p_item["estimated_cost_inr_per_100g"] / 100.0
                min_g, max_g = _serving_bounds(p_name, 0)
                cand_p_g = max(min_g, min(max_g, round(p_grams + (pro_res / pro_per_g), 0)))
                if cand_p_g <= p_grams or (_evaluate_plan_totals(raw_meal_specs)["cost_inr"] + (cand_p_g - p_grams) * cost_per_g) <= daily_budget_inr:
                    p_sp["items"][0][1] = cand_p_g

            # Fine-tune calories on Meal 2 carbohydrate staple
            residual_kcal = total_kcal - _evaluate_plan_totals(raw_meal_specs)["calories"]
            if abs(residual_kcal) >= 2:
                tune_sp = raw_meal_specs[1]
                t_name, t_grams = tune_sp["items"][1]
                t_item = FOOD_CATALOG_BY_NAME[t_name]
                kcal_per_g = t_item["calories_per_100g"] / 100.0
                cost_per_g = t_item["estimated_cost_inr_per_100g"] / 100.0
                min_g, max_g = _serving_bounds(t_name, 1)
                cand_c_g = max(min_g, min(max_g, round(t_grams + (residual_kcal / kcal_per_g), 0)))
                if cand_c_g <= t_grams or (_evaluate_plan_totals(raw_meal_specs)["cost_inr"] + (cand_c_g - t_grams) * cost_per_g) <= daily_budget_inr:
                    tune_sp["items"][1][1] = cand_c_g

        meals_out = []
        total_daily_cost = 0.0
        total_plan_cal = 0
        total_plan_pro = 0.0
        total_plan_carb = 0.0
        total_plan_fat = 0.0

        for sp in raw_meal_specs:
            ing_list = [compute_ingredient_from_db(f_name, f_grams) for f_name, f_grams in sp["items"]]
            m_cal = sum(int(i["calories"]) for i in ing_list)
            m_pro = round(sum(float(i["protein_g"]) for i in ing_list), 1)
            m_carb = round(sum(float(i["carbs_g"]) for i in ing_list), 1)
            m_fat = round(sum(float(i["fat_g"]) for i in ing_list), 1)
            m_cost = round(sum(float(i["cost_inr"]) for i in ing_list), 2)

            total_daily_cost += m_cost
            total_plan_cal += m_cal
            total_plan_pro += m_pro
            total_plan_carb += m_carb
            total_plan_fat += m_fat

            meals_out.append({
                "meal_number": sp["idx"],
                "name": sp["title"],
                "time_of_day": sp["time"],
                "target_calories": m_cal,
                "protein_g": m_pro,
                "carbs_g": m_carb,
                "fat_g": m_fat,
                "estimated_cost_inr": m_cost,
                "recipe_instructions": "Use measured raw/cooked weights on a kitchen scale. Cook with <= 1 tsp mustard/groundnut oil or ghee per meal.",
                "ingredients": ing_list,
            })

        estimated_weekly_cost = round(total_daily_cost * 7.0, 2)

        return {
            "plan_name": f"{dietary_type.title()} {total_kcal} kcal Indian Nutrition Plan",
            "daily_calories": total_kcal,
            "actual_meal_calories": total_plan_cal,
            "protein_grams": round(total_plan_pro, 1),
            "carbs_grams": round(total_plan_carb, 1),
            "fat_grams": round(total_plan_fat, 1),
            "estimated_daily_cost_inr": round(total_daily_cost, 2),
            "estimated_weekly_cost_inr": estimated_weekly_cost,
            "weekly_budget_inr": weekly_budget_inr,
            "meals": meals_out,
        }

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        context = envelope.context_data or {}
        summary = context.get("athlete_summary") or {}
        constraints = context.get("constraints") or {}

        # Always compute deterministic BMR/TDEE/Macro targets + goal/weight conflict detection first
        targets = calculate_nutrition_targets(
            weight_kg=float(summary.get("weight_kg", 70.0)),
            height_cm=float(summary.get("height_cm", 175.0)),
            age=int(summary.get("age", 25)),
            sex=str(summary.get("sex", "male")),
            activity_level=str(summary.get("activity_level", "moderately_active")),
            primary_goal=str(summary.get("primary_goal", "muscle_gain")),
            dietary_type=str(constraints.get("dietary_type", "omnivore")),
            target_weight_kg=summary.get("target_weight_kg"),
        )

        weekly_budget_inr = float(constraints.get("weekly_budget_inr") or 2500.0)
        det_plan = self._build_deterministic_meals(context, targets)
        provider = get_llm_provider()
        ai_resp = await provider.generate_structured_output(
            prompt=f"Synthesize meal plan matching targets {targets} and constraints {constraints}",
            system_instruction="You are a clinical sports nutritionist specializing in Indian and evidence-based diets.",
            response_schema=NutritionPlanLLMOutput,
        )

        meals_list = det_plan["meals"]
        if not ai_resp.is_fallback and ai_resp.data.meals:
            candidate_meals = [m.model_dump() for m in ai_resp.data.meals]
            cand_safety = validate_nutrition_plan_safety(
                target_calories=targets["target_calories"],
                bmr_kcal=targets["bmr_kcal"],
                tdee_kcal=targets["tdee_kcal"],
                allergies=constraints.get("allergies", []),
                meals=candidate_meals,
                weekly_budget_inr=weekly_budget_inr,
            )
            if cand_safety["is_valid"]:
                meals_list = candidate_meals

        safety = validate_nutrition_plan_safety(
            target_calories=targets["target_calories"],
            bmr_kcal=targets["bmr_kcal"],
            tdee_kcal=targets["tdee_kcal"],
            allergies=constraints.get("allergies", []),
            meals=meals_list,
            weekly_budget_inr=weekly_budget_inr,
        )

        explanation = (
            f"{targets['assumptions']} Meal plan structured for '{constraints.get('dietary_type', 'omnivore')}' diet "
            f"at ₹{det_plan['estimated_daily_cost_inr']}/day (₹{det_plan['estimated_weekly_cost_inr']}/week within ₹{det_plan['weekly_budget_inr']} budget). "
            + ("(Development Fallback Mode — Validated Database Macros Used)" if ai_resp.is_fallback else "")
        )

        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={
                "plan_name": det_plan["plan_name"],
                "targets": targets,
                "estimated_daily_cost_inr": det_plan["estimated_daily_cost_inr"],
                "estimated_weekly_cost_inr": det_plan["estimated_weekly_cost_inr"],
                "meals": meals_list,
                "safety_validation": safety,
            },
            explanation=explanation,
            validation_passed=safety["is_valid"],
            is_fallback=ai_resp.is_fallback,
        )
