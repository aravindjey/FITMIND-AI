"""Deterministic workout calculation engine: progressive overload, volume analysis,
recovery readiness scoring, and exercise prescriptions.
"""
from typing import Dict, Any, List, Optional
from app.engines.one_rep_max import estimate_1rm


def calculate_next_load_prescription(
    current_weight_kg: float,
    reps_completed: int,
    target_rep_min: int,
    target_rep_max: int,
    actual_rpe: Optional[float] = None,
    target_rpe: float = 8.0,
) -> Dict[str, Any]:
    """Deterministically computes next session's recommended weight and progression note
    using double progression + RPE autoregulation.
    """
    if current_weight_kg <= 0:
        return {
            "recommended_weight_kg": 0.0,
            "action": "maintain",
            "rationale": "Bodyweight or unweighted movement; progress by adding 1-2 reps per set."
        }

    rpe = actual_rpe if actual_rpe is not None else target_rpe

    # Case 1: Severe overshoot in RPE or missed minimum reps -> Micro-deload (-5%)
    if rpe >= target_rpe + 1.5 or reps_completed < target_rep_min:
        new_weight = round((current_weight_kg * 0.95) / 1.25) * 1.25
        return {
            "recommended_weight_kg": round(new_weight, 2),
            "action": "deload",
            "rationale": f"Actual RPE ({rpe}) exceeded target ({target_rpe}) or reps ({reps_completed}) fell below minimum ({target_rep_min}). Reduced load by ~5% to manage fatigue."
        }

    # Case 2: Hit top of rep range at or below target RPE -> Increase load (+2.5%, min +1.25kg)
    if reps_completed >= target_rep_max and rpe <= target_rpe + 0.5:
        increment = max(1.25, round((current_weight_kg * 0.025) / 1.25) * 1.25)
        new_weight = round(current_weight_kg + increment, 2)
        return {
            "recommended_weight_kg": new_weight,
            "action": "increase",
            "rationale": f"Completed {reps_completed} reps (>= {target_rep_max}) at RPE {rpe}. Apply progressive overload (+{increment} kg)."
        }

    # Case 3: Within target rep range -> Maintain load and push for +1 rep
    return {
        "recommended_weight_kg": round(current_weight_kg, 2),
        "action": "maintain_add_reps",
        "rationale": f"Completed {reps_completed} reps at RPE {rpe}. Maintain {current_weight_kg} kg and aim for {min(target_rep_max, reps_completed + 1)} reps next session."
    }


def calculate_session_volume(set_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculates total working tonnage (kg), working sets count, and peak estimated 1RM."""
    total_volume = 0.0
    working_sets = 0
    peak_1rm = 0.0

    for s in set_logs:
        if s.get("is_warmup", False):
            continue
        w = float(s.get("weight_kg", 0.0))
        r = int(s.get("reps_completed", 0))
        working_sets += 1
        total_volume += w * r
        est = estimate_1rm(w, r)
        if est > peak_1rm:
            peak_1rm = est

    return {
        "total_volume_kg": round(total_volume, 2),
        "working_sets": working_sets,
        "peak_estimated_1rm_kg": round(peak_1rm, 2),
    }


def calculate_recovery_readiness(
    sleep_hours: float,
    sleep_quality_score: int,
    energy_score: int,
    soreness_score: int,
    stress_score: int,
) -> Dict[str, Any]:
    """Deterministically calculates a 0-100 daily recovery readiness score and training modifier.
    - Sleep duration optimal: 7.5-9.0 hours (35% weight)
    - Sleep quality (1-10): 20% weight
    - Energy score (1-10): 20% weight
    - Soreness score (1-10, lower is better): 15% weight
    - Stress score (1-10, lower is better): 10% weight
    """
    sleep_norm = min(1.0, max(0.0, sleep_hours / 8.0)) * 100.0
    quality_norm = min(10, max(1, sleep_quality_score)) * 10.0
    energy_norm = min(10, max(1, energy_score)) * 10.0
    soreness_inv = (11 - min(10, max(1, soreness_score))) * 10.0
    stress_inv = (11 - min(10, max(1, stress_score))) * 10.0

    readiness = int(round(
        (sleep_norm * 0.35)
        + (quality_norm * 0.20)
        + (energy_norm * 0.20)
        + (soreness_inv * 0.15)
        + (stress_inv * 0.10)
    ))
    readiness = max(1, min(100, readiness))

    if readiness >= 80:
        status = "optimal"
        intensity_modifier = 1.0
        recommendation = "Readiness is high. Execute prescribed working sets and progressive overload targets as planned."
    elif readiness >= 60:
        status = "moderate"
        intensity_modifier = 0.95
        recommendation = "Moderate readiness. Train as scheduled but cap top sets at RPE 8 (leave 2 reps in reserve)."
    else:
        status = "low_recovery_deload"
        intensity_modifier = 0.85
        recommendation = "Elevated fatigue or sleep debt detected. Reduce working weights by 10-15% or cut 1 set per exercise today, and prioritize 8+ hours of sleep."

    return {
        "readiness_score": readiness,
        "status": status,
        "intensity_modifier": intensity_modifier,
        "recommendation": recommendation,
    }
