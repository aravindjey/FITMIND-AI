"""Configurable Safety & Validation Engine.
Validates nutrition and workout plans against athlete-specific BMR, TDEE, allergies,
volume ceilings, and equipment constraints.
"""
from typing import Dict, Any, List
from app.core.config import settings


def validate_nutrition_plan_safety(
    target_calories: int,
    bmr_kcal: int,
    tdee_kcal: int,
    allergies: List[str],
    meals: List[Dict[str, Any]],
) -> Dict[str, Any]:
    violations: List[str] = []
    warnings: List[str] = []

    min_floor = int(round(max(bmr_kcal * settings.SAFETY_MIN_BMR_MULTIPLIER, settings.SAFETY_ABSOLUTE_MIN_CALORIES)))
    if target_calories < min_floor:
        violations.append(
            f"Target calories ({target_calories} kcal) fell below configured safety floor ({min_floor} kcal)."
        )

    if tdee_kcal > 0:
        deficit_pct = (tdee_kcal - target_calories) / float(tdee_kcal)
        if deficit_pct > settings.SAFETY_MAX_DAILY_DEFICIT_PERCENT:
            violations.append(
                f"Caloric deficit ({deficit_pct*100:.1f}%) exceeds maximum configured safe deficit ({settings.SAFETY_MAX_DAILY_DEFICIT_PERCENT*100:.0f}%)."
            )

    # Check meals against allergies
    normalized_allergies = [a.lower().strip() for a in allergies if a.strip()]
    for meal in meals:
        meal_name = meal.get("name", "Meal")
        ingredients = meal.get("ingredients", [])
        for ing in ingredients:
            ing_name = str(ing.get("name", "")).lower()
            for allergy in normalized_allergies:
                if allergy and allergy in ing_name:
                    violations.append(
                        f"Allergen violation: '{ing.get('name')}' in '{meal_name}' matches declared allergy '{allergy}'."
                    )

    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "requires_medical_escalation": len(violations) > 0 and target_calories < 1100,
    }


def validate_workout_plan_safety(
    workout_days: List[Dict[str, Any]],
    available_equipment: List[str],
    max_sets_per_session: int = 28,
) -> Dict[str, Any]:
    violations: List[str] = []
    warnings: List[str] = []

    norm_equip = {e.lower().strip() for e in available_equipment if e.strip()}
    # Bodyweight is always available
    norm_equip.add("bodyweight")

    for day in workout_days:
        day_name = day.get("name", f"Day {day.get('day_number', 1)}")
        exercises = day.get("exercises", [])
        total_sets = sum(int(ex.get("target_sets", 0)) for ex in exercises)
        if total_sets > max_sets_per_session:
            violations.append(
                f"Session '{day_name}' prescribes {total_sets} working sets, exceeding safe session ceiling of {max_sets_per_session} sets."
            )
        for ex in exercises:
            req_eq = str(ex.get("equipment_required", "bodyweight")).lower().strip()
            if norm_equip and req_eq not in norm_equip and "full_gym" not in norm_equip:
                warnings.append(
                    f"Exercise '{ex.get('exercise_name')}' requires '{req_eq}', which is not in user's primary equipment list."
                )

    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
    }
