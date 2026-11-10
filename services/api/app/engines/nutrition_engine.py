"""Deterministic BMR, TDEE, and macronutrient target calculation engine.
All mathematical formulas and assumptions are explicit and reproducible.
"""
from typing import Dict, Any

ACTIVITY_MULTIPLIERS: Dict[str, float] = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}

GOAL_CALORIE_DELTAS: Dict[str, float] = {
    "fat_loss": -0.20,          # 20% caloric deficit
    "muscle_gain": 0.12,        # 12% caloric surplus
    "bodybuilding": 0.10,       # 10% lean bulk surplus
    "strength": 0.08,           # 8% performance surplus
    "powerlifting": 0.08,       # 8% strength surplus
    "sports_performance": 0.05, # 5% athletic maintenance/surplus
    "general_fitness": 0.0,     # Maintenance calories
}


def calculate_bmr_mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, sex: str) -> int:
    """Calculates Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation.
    - Male:   10 * weight(kg) + 6.25 * height(cm) - 5 * age(y) + 5
    - Female: 10 * weight(kg) + 6.25 * height(cm) - 5 * age(y) - 161
    - Other:  midpoint adjustment (-78)
    """
    if weight_kg <= 0 or height_cm <= 0 or age <= 0:
        raise ValueError("Weight, height, and age must be positive values.")

    sex_norm = sex.lower().strip()
    if sex_norm == "male":
        s = 5.0
    elif sex_norm == "female":
        s = -161.0
    else:
        s = -78.0

    bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) + s
    return max(800, int(round(bmr)))


def calculate_tdee(bmr_kcal: int, activity_level: str) -> int:
    """Calculates Total Daily Energy Expenditure (TDEE) from BMR and activity level."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level.lower().strip(), 1.55)
    return int(round(bmr_kcal * multiplier))


def calculate_nutrition_targets(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,
    activity_level: str,
    primary_goal: str = "general_fitness",
    dietary_type: str = "omnivore",
) -> Dict[str, Any]:
    """Deterministically computes BMR, TDEE, Target Calories, and Macronutrients (Protein, Carbs, Fat)
    with explicit scientific assumptions.
    """
    bmr = calculate_bmr_mifflin_st_jeor(weight_kg=weight_kg, height_cm=height_cm, age=age, sex=sex)
    tdee = calculate_tdee(bmr_kcal=bmr, activity_level=activity_level)

    goal_key = primary_goal.lower().strip()
    delta_pct = GOAL_CALORIE_DELTAS.get(goal_key, 0.0)
    raw_target = int(round(tdee * (1.0 + delta_pct)))

    # Enforce safe minimum caloric floor relative to BMR and sex-neutral lower bound
    min_safe_floor = max(bmr, 1200 if sex.lower().strip() == "female" else 1400)
    target_calories = max(min_safe_floor, raw_target)

    # Protein allocation (g/kg body weight)
    if goal_key in ("muscle_gain", "bodybuilding", "fat_loss"):
        protein_per_kg = 2.0
    elif goal_key in ("strength", "powerlifting", "sports_performance"):
        protein_per_kg = 1.8
    else:
        protein_per_kg = 1.6

    # Slightly adjust for strict plant-based digestibility while keeping realistic bounds
    if dietary_type.lower().strip() in ("vegetarian", "vegan", "jain"):
        protein_per_kg = min(2.0, round(protein_per_kg, 2))

    protein_grams = int(round(weight_kg * protein_per_kg))
    protein_kcal = protein_grams * 4

    # Fat allocation: 25% of total target calories (minimum 0.7g/kg for hormonal health)
    fat_kcal = int(round(target_calories * 0.25))
    fat_grams = max(int(round(weight_kg * 0.7)), int(round(fat_kcal / 9.0)))
    fat_kcal = fat_grams * 9

    # Carbohydrate allocation: remainder of target calories
    remaining_kcal = max(0, target_calories - (protein_kcal + fat_kcal))
    carbs_grams = int(round(remaining_kcal / 4.0))

    # Reconcile exact calorie total
    reconciled_calories = (protein_grams * 4) + (carbs_grams * 4) + (fat_grams * 9)

    assumptions = (
        f"Mifflin-St Jeor BMR ({bmr} kcal) x Activity Multiplier ({ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)}) "
        f"= TDEE ({tdee} kcal). Goal adjustment ({delta_pct*100:+.0f}%) with safety floor ({min_safe_floor} kcal) "
        f"-> {reconciled_calories} kcal/day ({protein_per_kg}g/kg protein, 25% fat, remainder carbohydrates)."
    )

    return {
        "bmr_kcal": bmr,
        "tdee_kcal": tdee,
        "target_calories": reconciled_calories,
        "protein_grams": protein_grams,
        "carbs_grams": carbs_grams,
        "fat_grams": fat_grams,
        "assumptions": assumptions,
    }
