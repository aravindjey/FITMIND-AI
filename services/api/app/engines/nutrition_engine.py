"""Deterministic BMR, TDEE, and macronutrient target calculation engine.
All mathematical formulas and assumptions are explicit and reproducible.
"""
from typing import Dict, Any, Optional, List

ACTIVITY_MULTIPLIERS: Dict[str, float] = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
    "extra_active": 1.9,
}

GOAL_CALORIE_DELTAS: Dict[str, float] = {
    "fat_loss": -0.20,           # 20% caloric deficit
    "muscle_gain": 0.12,         # 12% caloric surplus (when target_weight >= current_weight)
    "bodybuilding": 0.10,        # 10% lean bulk surplus (when target_weight >= current_weight)
    "strength": 0.08,            # 8% performance surplus
    "powerlifting": 0.08,        # 8% strength surplus
    "sports_performance": 0.05,  # 5% athletic maintenance/surplus
    "general_fitness": 0.0,      # Maintenance calories
}


def detect_goal_weight_conflict(
    current_weight_kg: float,
    target_weight_kg: Optional[float],
    primary_goal: str,
) -> Dict[str, Any]:
    """Detects contradictions between an athlete's current weight, target weight, and primary goal.
    Returns structured conflict metadata, effective calorie regime, and an explicit warning/clarification notice.
    """
    goal_key = primary_goal.lower().strip()
    if target_weight_kg is None or target_weight_kg <= 0:
        return {
            "has_conflict": False,
            "effective_regime": goal_key,
            "weight_delta_kg": 0.0,
            "warning": None,
        }

    weight_delta = round(float(target_weight_kg) - float(current_weight_kg), 2)

    # Case 1: Hypertrophy / Strength / Bulk goal selected, but target weight is > 1.0 kg BELOW current weight
    if goal_key in ("muscle_gain", "bodybuilding", "strength", "powerlifting") and weight_delta < -1.0:
        warning = (
            f"GOAL / TARGET WEIGHT CONFLICT DETECTED: Primary goal is '{goal_key.replace('_', ' ')}', "
            f"but target weight ({target_weight_kg} kg) is {abs(weight_delta):.1f} kg BELOW current weight ({current_weight_kg} kg). "
            f"A caloric surplus (+10-12%) would increase body weight further away from {target_weight_kg} kg. "
            f"Automatically applying a high-protein Body Recomposition / Lean Cut deficit (-15% TDEE, 2.2g/kg protein) "
            f"so you can reduce body weight toward {target_weight_kg} kg while preserving/building lean muscle mass. "
            f"Please clarify in your Profile if you intended to bulk above {current_weight_kg} kg or cut to {target_weight_kg} kg."
        )
        return {
            "has_conflict": True,
            "effective_regime": "recomposition_cut",
            "weight_delta_kg": weight_delta,
            "warning": warning,
        }

    # Case 2: Fat Loss goal selected, but target weight is > 1.0 kg ABOVE current weight
    if goal_key == "fat_loss" and weight_delta > 1.0:
        warning = (
            f"GOAL / TARGET WEIGHT CONFLICT DETECTED: Primary goal is 'fat loss', "
            f"but target weight ({target_weight_kg} kg) is {weight_delta:+.1f} kg ABOVE current weight ({current_weight_kg} kg). "
            f"A -20% fat-loss deficit will decrease body weight rather than reach {target_weight_kg} kg. "
            f"Please clarify in your Profile whether your priority is fat loss or lean weight gain to {target_weight_kg} kg."
        )
        return {
            "has_conflict": True,
            "effective_regime": "fat_loss",
            "weight_delta_kg": weight_delta,
            "warning": warning,
        }

    # Case 3: General fitness with significant weight loss target
    if goal_key == "general_fitness" and weight_delta < -1.5:
        return {
            "has_conflict": False,
            "effective_regime": "recomposition_cut",
            "weight_delta_kg": weight_delta,
            "warning": (
                f"Target weight ({target_weight_kg} kg) is {abs(weight_delta):.1f} kg below current weight ({current_weight_kg} kg); "
                f"applying a moderate -15% caloric deficit."
            ),
        }

    return {
        "has_conflict": False,
        "effective_regime": goal_key,
        "weight_delta_kg": weight_delta,
        "warning": None,
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
    target_weight_kg: Optional[float] = None,
) -> Dict[str, Any]:
    """Deterministically computes BMR, TDEE, Target Calories, and Macronutrients (Protein, Carbs, Fat)
    with explicit scientific assumptions and target-weight consistency checks.
    """
    bmr = calculate_bmr_mifflin_st_jeor(weight_kg=weight_kg, height_cm=height_cm, age=age, sex=sex)
    tdee = calculate_tdee(bmr_kcal=bmr, activity_level=activity_level)

    goal_key = primary_goal.lower().strip()
    conflict_info = detect_goal_weight_conflict(
        current_weight_kg=weight_kg,
        target_weight_kg=target_weight_kg,
        primary_goal=goal_key,
    )

    effective_regime = conflict_info["effective_regime"]
    if effective_regime == "recomposition_cut":
        delta_pct = -0.15  # 15% deficit for recomposition when target weight < current weight
    else:
        delta_pct = GOAL_CALORIE_DELTAS.get(goal_key, 0.0)

    raw_target = int(round(tdee * (1.0 + delta_pct)))

    # Enforce safe minimum caloric floor relative to BMR and sex-neutral lower bound
    min_safe_floor = max(bmr, 1200 if sex.lower().strip() == "female" else 1400)
    target_calories = max(min_safe_floor, raw_target)

    # Protein allocation (g/kg body weight)
    if effective_regime == "recomposition_cut":
        protein_per_kg = 2.1
    elif goal_key in ("muscle_gain", "bodybuilding", "fat_loss"):
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

    fiber_grams = max(25, min(45, int(round((reconciled_calories / 1000.0) * 14))))
    hydration_liters = round(max(2.5, weight_kg * 0.04), 2)

    warnings: List[str] = []
    if conflict_info["warning"]:
        warnings.append(conflict_info["warning"])

    assumptions = (
        f"Mifflin-St Jeor BMR ({bmr} kcal) x Activity Multiplier ({ACTIVITY_MULTIPLIERS.get(activity_level.lower().strip(), 1.55)}) "
        f"= TDEE ({tdee} kcal). Goal adjustment ({delta_pct*100:+.0f}% [{effective_regime}]) with safety floor ({min_safe_floor} kcal) "
        f"-> {reconciled_calories} kcal/day ({protein_per_kg}g/kg protein, 25% fat, remainder carbohydrates)."
    )
    if conflict_info["warning"]:
        assumptions = f"{conflict_info['warning']} | {assumptions}"

    return {
        "bmr_kcal": bmr,
        "tdee_kcal": tdee,
        "target_calories": reconciled_calories,
        "calorie_adjustment_percent": round(delta_pct * 100, 1),
        "effective_regime": effective_regime,
        "goal_weight_conflict": conflict_info["has_conflict"],
        "goal_conflict_warning": conflict_info["warning"],
        "warnings": warnings,
        "protein_grams": protein_grams,
        "carbs_grams": carbs_grams,
        "fat_grams": fat_grams,
        "fiber_grams": fiber_grams,
        "hydration_liters": hydration_liters,
        "assumptions": assumptions,
    }
