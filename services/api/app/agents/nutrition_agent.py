from typing import Dict, Any, List
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentInputEnvelope, AgentOutputEnvelope
from app.ai.factory import get_llm_provider
from app.engines.nutrition_engine import calculate_nutrition_targets
from app.engines.safety_engine import validate_nutrition_plan_safety


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
    allergen-safe, INR-budget-aware meal plans.
    """

    @property
    def agent_name(self) -> str:
        return "NutritionAgent"

    def _build_deterministic_meals(self, context: Dict[str, Any], targets: Dict[str, Any]) -> Dict[str, Any]:
        constraints = context.get("constraints") or {}
        dietary_type = str(constraints.get("dietary_type", "omnivore")).lower()
        meals_per_day = int(constraints.get("meals_per_day", 4))
        allergies = [a.lower().strip() for a in constraints.get("allergies", [])]
        disliked = [d.lower().strip() for d in constraints.get("disliked_foods", [])]
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

        # Select culturally appropriate Indian staple protein, carb, and fat sources respecting restrictions
        if is_vegan or has_dairy_allergy:
            pro_breakfast = ("Soya Chunks Bhurji (Dry Weight)", 50.0, 172, 26.0, 16.5, 0.3, 10.0) if not has_soy_allergy else ("Moong Dal Chilla / Sprouts", 180.0, 209, 13.0, 31.5, 3.8, 18.0)
            pro_lunch = ("Rajma / Chana Masala (Cooked)", 250.0, 350, 21.0, 52.5, 6.5, 30.0)
            pro_snack = ("Roasted Chana & Sprouts Bowl", 100.0, 160, 11.0, 24.0, 2.5, 15.0)
            pro_dinner = ("Moong / Toor Dal Tadka (Cooked)", 250.0, 290, 18.0, 43.8, 5.2, 25.0)
        elif is_veg:
            pro_breakfast = ("Whey Protein Isolate / Concentrate", 35.0, 136, 28.0, 2.8, 1.6, 75.0) if daily_budget_inr >= 250 else ("Low-Fat Paneer Bhurji", 100.0, 215, 20.0, 3.5, 13.5, 45.0)
            pro_lunch = ("Low-Fat Paneer / Cottage Cheese + Dal", 120.0, 258, 24.0, 4.2, 16.2, 54.0)
            pro_snack = ("Soya Chunks Masala (Dry Weight)", 50.0, 172, 26.0, 16.5, 0.3, 10.0) if not has_soy_allergy else ("Dahi / Toned Milk Curd Bowl", 250.0, 155, 9.5, 11.8, 7.5, 25.0)
            pro_dinner = ("Moong / Toor Dal Tadka + Dahi", 250.0, 290, 18.0, 43.8, 5.2, 25.0)
        else:
            pro_breakfast = ("Whole Boiled Eggs (3 Large)", 150.0, 232, 18.9, 1.6, 15.9, 24.0) if not has_egg_allergy else ("Low-Fat Paneer Bhurji", 100.0, 215, 20.0, 3.5, 13.5, 45.0)
            pro_lunch = ("Chicken Breast (Grilled / Home Curry)", 160.0, 264, 49.6, 0.0, 5.8, 60.0)
            pro_snack = ("Whey Protein Shake or Egg Whites", 30.0, 117, 24.0, 2.4, 1.4, 65.0) if not has_dairy_allergy else ("Boiled Egg Whites & Chana", 150.0, 130, 18.0, 10.0, 1.5, 24.0)
            pro_dinner = ("Chicken Breast / Rohu Fish Curry", 150.0, 248, 46.5, 0.0, 5.4, 57.0)

        nut_addition = (
            ("Mixed Pumpkin & Sunflower Seeds", 20.0, 115, 5.0, 3.0, 9.5, 12.0)
            if has_peanut_allergy
            else ("Roasted Peanuts / Natural Peanut Butter", 25.0, 147, 6.5, 4.0, 12.3, 8.0)
        )

        # Scale carbohydrate portions to match athlete's exact caloric/macro target
        meal_templates = [
            ("Meal 1: High-Protein Indian Breakfast", "08:00 AM", pro_breakfast, ("Rolled Oats / Poha Base", 70.0, 272, 11.8, 46.4, 4.8, 15.0)),
            ("Meal 2: Balanced Indian Thali Lunch", "01:30 PM", pro_lunch, ("Steamed Basmati Rice (Cooked)", 220.0, 286, 5.9, 62.0, 0.7, 13.0)),
            ("Meal 3: Pre/Post-Workout Fuel Snack", "05:30 PM", pro_snack, ("Ripe Banana", 120.0, 107, 1.3, 27.4, 0.4, 7.0)),
            ("Meal 4: Recovery Dinner", "09:00 PM", pro_dinner, ("Whole Wheat Roti / Chapati (Cooked)", 100.0, 297, 9.6, 58.0, 3.0, 8.0)),
        ]

        selected_templates = meal_templates[:max(1, min(4, meals_per_day))]
        scale_factor = max(0.65, min(1.8, total_kcal / 2050.0))

        meals_out = []
        total_daily_cost = 0.0

        for idx, (m_title, m_time, pro_tuple, carb_tuple) in enumerate(selected_templates, start=1):
            p_name, p_g, p_cal, p_pro, p_carb, p_fat, p_cost = pro_tuple
            c_name, c_g, c_cal, c_pro, c_carb, c_fat, c_cost = carb_tuple

            # Scale carb & protein quantities proportionally
            c_mult = scale_factor
            p_mult = max(0.85, min(1.5, total_pro / 135.0))

            ing_list = [
                {
                    "name": p_name,
                    "quantity_grams": round(p_g * p_mult, 0),
                    "preparation_state": "cooked",
                    "calories": int(round(p_cal * p_mult)),
                    "protein_g": round(p_pro * p_mult, 1),
                    "carbs_g": round(p_carb * p_mult, 1),
                    "fat_g": round(p_fat * p_mult, 1),
                    "cost_inr": round(p_cost * p_mult, 1),
                },
                {
                    "name": c_name,
                    "quantity_grams": round(c_g * c_mult, 0),
                    "preparation_state": "cooked",
                    "calories": int(round(c_cal * c_mult)),
                    "protein_g": round(c_pro * c_mult, 1),
                    "carbs_g": round(c_carb * c_mult, 1),
                    "fat_g": round(c_fat * c_mult, 1),
                    "cost_inr": round(c_cost * c_mult, 1),
                },
                {
                    "name": "Mixed Seasonal Sabzi (Palak, Gobhi, Beans)",
                    "quantity_grams": 150.0,
                    "preparation_state": "cooked",
                    "calories": 108,
                    "protein_g": 3.9,
                    "carbs_g": 14.1,
                    "fat_g": 4.2,
                    "cost_inr": 12.0,
                } if idx in (2, 4) else {
                    "name": nut_addition[0],
                    "quantity_grams": nut_addition[1],
                    "preparation_state": "ready_to_eat",
                    "calories": nut_addition[2],
                    "protein_g": nut_addition[3],
                    "carbs_g": nut_addition[4],
                    "fat_g": nut_addition[5],
                    "cost_inr": nut_addition[6],
                }
            ]

            m_cal = sum(int(i["calories"]) for i in ing_list)
            m_pro = int(round(sum(float(i["protein_g"]) for i in ing_list)))
            m_carb = int(round(sum(float(i["carbs_g"]) for i in ing_list)))
            m_fat = int(round(sum(float(i["fat_g"]) for i in ing_list)))
            m_cost = round(sum(float(i["cost_inr"]) for i in ing_list), 2)
            total_daily_cost += m_cost

            meals_out.append({
                "meal_number": idx,
                "name": m_title,
                "time_of_day": m_time,
                "target_calories": m_cal,
                "protein_g": m_pro,
                "carbs_g": m_carb,
                "fat_g": m_fat,
                "estimated_cost_inr": m_cost,
                "recipe_instructions": "Use measured raw/cooked weights on a kitchen scale. Cook with <= 1 tsp mustard/groundnut oil or ghee per meal.",
                "ingredients": ing_list,
            })

        return {
            "plan_name": f"{dietary_type.title()} {total_kcal} kcal Indian Nutrition Plan",
            "daily_calories": total_kcal,
            "protein_grams": total_pro,
            "carbs_grams": total_carb,
            "fat_grams": total_fat,
            "estimated_daily_cost_inr": round(total_daily_cost, 2),
            "weekly_budget_inr": weekly_budget_inr,
            "meals": meals_out,
        }

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        context = envelope.context_data or {}
        summary = context.get("athlete_summary") or {}
        constraints = context.get("constraints") or {}

        # Always compute deterministic BMR/TDEE/Macro targets first
        targets = calculate_nutrition_targets(
            weight_kg=float(summary.get("weight_kg", 70.0)),
            height_cm=float(summary.get("height_cm", 175.0)),
            age=int(summary.get("age", 25)),
            sex=str(summary.get("sex", "male")),
            activity_level=str(summary.get("activity_level", "moderately_active")),
            primary_goal=str(summary.get("primary_goal", "muscle_gain")),
            dietary_type=str(constraints.get("dietary_type", "omnivore")),
        )

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
            )
            if cand_safety["is_valid"]:
                meals_list = candidate_meals

        safety = validate_nutrition_plan_safety(
            target_calories=targets["target_calories"],
            bmr_kcal=targets["bmr_kcal"],
            tdee_kcal=targets["tdee_kcal"],
            allergies=constraints.get("allergies", []),
            meals=meals_list,
        )

        explanation = (
            f"{targets['assumptions']} Meal plan structured for '{constraints.get('dietary_type', 'omnivore')}' diet "
            f"at ~₹{det_plan['estimated_daily_cost_inr']}/day (weekly budget: ₹{det_plan['weekly_budget_inr']}). "
            + ("(Development Fallback Mode — Validated Database Macros Used)" if ai_resp.is_fallback else "")
        )

        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={
                "plan_name": det_plan["plan_name"],
                "targets": targets,
                "estimated_daily_cost_inr": det_plan["estimated_daily_cost_inr"],
                "meals": meals_list,
                "safety_validation": safety,
            },
            explanation=explanation,
            validation_passed=safety["is_valid"],
            is_fallback=ai_resp.is_fallback,
        )
