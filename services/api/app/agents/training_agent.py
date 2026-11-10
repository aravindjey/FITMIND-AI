from typing import Dict, Any, List
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentInputEnvelope, AgentOutputEnvelope
from app.ai.factory import get_llm_provider
from app.engines.safety_engine import validate_workout_plan_safety


class PlannedExerciseSchema(BaseModel):
    exercise_name: str = "Barbell Back Squat"
    equipment_required: str = "barbell"
    order_in_workout: int = 1
    target_sets: int = 3
    target_rep_range_min: int = 6
    target_rep_range_max: int = 10
    prescribed_weight_kg: float = 40.0
    target_rpe: float = 8.0
    rest_seconds: int = 120
    tempo: str = "2-0-1-0"
    progression_rule: str = "Add 2.5 kg when all sets hit top of rep range at <= RPE 8"
    notes: str = "Focus on controlled eccentric and full range of motion."


class PlannedDaySchema(BaseModel):
    day_number: int = 1
    name: str = "Day 1 - Upper Body Strength"
    target_focus: str = "Chest, Back, Shoulders"
    scheduled_weekday: str = "Mon"
    exercises: List[PlannedExerciseSchema] = Field(default_factory=list)


class WorkoutPlanLLMOutput(BaseModel):
    plan_name: str = "Personalized Periodized Training Program"
    training_split: str = "upper_lower"
    duration_weeks: int = 4
    explanation: str = "Periodized program tailored to athlete goal, equipment, and recovery readiness."
    days: List[PlannedDaySchema] = Field(default_factory=list)


class TrainingAgent(BaseAgent):
    """Component #2: Workout Planning Agent.
    Synthesizes personalized training programs respecting equipment, goal, experience,
    PRs, and deterministic progression/safety rules.
    """

    @property
    def agent_name(self) -> str:
        return "TrainingAgent"

    def _build_deterministic_program(self, context: Dict[str, Any]) -> Dict[str, Any]:
        summary = context.get("athlete_summary") or {}
        constraints = context.get("constraints") or {}
        recovery = context.get("recent_recovery") or {}
        prs = {p["exercise_name"]: p["estimated_1rm_kg"] for p in context.get("personal_records", [])}

        goal = summary.get("primary_goal", "muscle_gain")
        exp_years = float(summary.get("training_experience_years", 1.0))
        weight_kg = float(summary.get("weight_kg", 70.0))
        days_per_week = int(constraints.get("days_per_week", 4))
        equipment = [e.lower() for e in constraints.get("equipment", ["bodyweight", "dumbbell", "barbell"])]
        preferred_days = constraints.get("preferred_days", ["Mon", "Tue", "Thu", "Fri", "Sat"])
        intensity_mod = float(recovery.get("intensity_modifier", 1.0))

        has_barbell = "barbell" in equipment or "full_gym" in equipment
        has_dumbbell = "dumbbell" in equipment or "full_gym" in equipment
        has_cables = "cables" in equipment or "machine" in equipment or "full_gym" in equipment

        # Rep & set scheme by goal
        if goal in ("strength", "powerlifting"):
            main_reps = (3, 5)
            acc_reps = (6, 10)
            main_sets = 4 if exp_years >= 1.0 else 3
            main_rest = 180
            split_name = "powerlifting" if goal == "powerlifting" else "strength_upper_lower"
        elif goal in ("muscle_gain", "bodybuilding"):
            main_reps = (6, 10)
            acc_reps = (10, 15)
            main_sets = 4 if exp_years >= 1.5 else 3
            main_rest = 120
            split_name = "push_pull_legs" if days_per_week >= 5 else "upper_lower"
        else:
            main_reps = (8, 12)
            acc_reps = (12, 15)
            main_sets = 3
            main_rest = 90
            split_name = "full_body" if days_per_week <= 3 else "upper_lower"

        def _prescribe_load(ex_name: str, bw_ratio: float) -> float:
            if "bodyweight" in ex_name.lower() or "push-up" in ex_name.lower() or "pull-up" in ex_name.lower() or "plank" in ex_name.lower() or "bridge" in ex_name.lower():
                return 0.0
            if ex_name in prs and prs[ex_name] > 0:
                base = prs[ex_name] * 0.77
            else:
                exp_factor = 1.0 + min(0.5, exp_years * 0.1)
                base = weight_kg * bw_ratio * exp_factor
            adjusted = base * intensity_mod
            return max(5.0, round(adjusted / 2.5) * 2.5)

        upper_a = [
            {
                "exercise_name": "Barbell Bench Press" if has_barbell else ("Incline Dumbbell Press" if has_dumbbell else "Push-Ups"),
                "equipment_required": "barbell" if has_barbell else ("dumbbell" if has_dumbbell else "bodyweight"),
                "target_sets": main_sets,
                "target_rep_range_min": main_reps[0],
                "target_rep_range_max": main_reps[1],
                "prescribed_weight_kg": _prescribe_load("Barbell Bench Press", 0.65 if has_barbell else 0.25),
                "target_rpe": 8.0,
                "rest_seconds": main_rest,
                "tempo": "2-1-1-0",
                "progression_rule": "Increase by 2.5 kg once all sets reach top of rep range at <= RPE 8",
                "notes": "Primary horizontal press movement."
            },
            {
                "exercise_name": "Barbell Bent-Over Row" if has_barbell else ("One-Arm Dumbbell Row" if has_dumbbell else "Pull-Ups / Chin-Ups"),
                "equipment_required": "barbell" if has_barbell else ("dumbbell" if has_dumbbell else "bodyweight"),
                "target_sets": main_sets,
                "target_rep_range_min": main_reps[0],
                "target_rep_range_max": main_reps[1],
                "prescribed_weight_kg": _prescribe_load("Barbell Bent-Over Row", 0.60 if has_barbell else 0.25),
                "target_rpe": 8.0,
                "rest_seconds": 120,
                "tempo": "2-0-1-1",
                "progression_rule": "Double progression within rep range",
                "notes": "Maintain neutral spine and retract scapulae."
            },
            {
                "exercise_name": "Seated Dumbbell Shoulder Press" if has_dumbbell else ("Overhead Barbell Press" if has_barbell else "Pike Push-Ups"),
                "equipment_required": "dumbbell" if has_dumbbell else ("barbell" if has_barbell else "bodyweight"),
                "target_sets": 3,
                "target_rep_range_min": acc_reps[0],
                "target_rep_range_max": acc_reps[1],
                "prescribed_weight_kg": _prescribe_load("Seated Dumbbell Shoulder Press", 0.20 if has_dumbbell else 0.45),
                "target_rpe": 8.0,
                "rest_seconds": 90,
                "tempo": "2-0-1-0",
                "progression_rule": "Add 1 rep per set weekly until top of range",
                "notes": "Control full shoulder ROM."
            },
            {
                "exercise_name": "Dumbbell Bicep Curl" if has_dumbbell else "Pull-Ups / Chin-Ups",
                "equipment_required": "dumbbell" if has_dumbbell else "bodyweight",
                "target_sets": 3,
                "target_rep_range_min": 10,
                "target_rep_range_max": 15,
                "prescribed_weight_kg": _prescribe_load("Dumbbell Bicep Curl", 0.14),
                "target_rpe": 8.5,
                "rest_seconds": 60,
                "tempo": "2-0-1-1",
                "progression_rule": "Increase weight when 15 reps achieved across all sets",
                "notes": "Strict elbow position."
            },
        ]

        lower_a = [
            {
                "exercise_name": "Barbell Back Squat" if has_barbell else ("Dumbbell Goblet Squat" if has_dumbbell else "Bodyweight Squat"),
                "equipment_required": "barbell" if has_barbell else ("dumbbell" if has_dumbbell else "bodyweight"),
                "target_sets": main_sets,
                "target_rep_range_min": main_reps[0],
                "target_rep_range_max": main_reps[1],
                "prescribed_weight_kg": _prescribe_load("Barbell Back Squat", 0.85 if has_barbell else 0.35),
                "target_rpe": 8.0,
                "rest_seconds": main_rest,
                "tempo": "3-0-1-0",
                "progression_rule": "Add 2.5 kg when all sets hit top of rep range at <= RPE 8",
                "notes": "Primary knee-dominant compound lift."
            },
            {
                "exercise_name": "Romanian Deadlift (Barbell)" if has_barbell else ("Dumbbell Romanian Deadlift" if has_dumbbell else "Glute Bridge / Hip Thrust"),
                "equipment_required": "barbell" if has_barbell else ("dumbbell" if has_dumbbell else "bodyweight"),
                "target_sets": 3,
                "target_rep_range_min": 8,
                "target_rep_range_max": 12,
                "prescribed_weight_kg": _prescribe_load("Romanian Deadlift (Barbell)", 0.75 if has_barbell else 0.30),
                "target_rpe": 8.0,
                "rest_seconds": 120,
                "tempo": "3-1-1-0",
                "progression_rule": "Add 2.5 kg after hitting 12 reps on all sets",
                "notes": "Hinge at hips keeping neutral lumbar spine."
            },
            {
                "exercise_name": "Bulgarian Split Squat" if has_dumbbell else "Bodyweight Squat",
                "equipment_required": "dumbbell" if has_dumbbell else "bodyweight",
                "target_sets": 3,
                "target_rep_range_min": 8,
                "target_rep_range_max": 12,
                "prescribed_weight_kg": _prescribe_load("Bulgarian Split Squat", 0.20),
                "target_rpe": 8.0,
                "rest_seconds": 90,
                "tempo": "2-0-1-0",
                "progression_rule": "Unilateral leg progression",
                "notes": "Addresses left-to-right lower body symmetry."
            },
            {
                "exercise_name": "Plank Hold",
                "equipment_required": "bodyweight",
                "target_sets": 3,
                "target_rep_range_min": 45,
                "target_rep_range_max": 60,
                "prescribed_weight_kg": 0.0,
                "target_rpe": 8.0,
                "rest_seconds": 60,
                "tempo": "isometric",
                "progression_rule": "Add 5 seconds per week",
                "notes": "Target reps represent seconds held."
            },
        ]

        upper_b = [
            {
                "exercise_name": "Overhead Barbell Press" if has_barbell else ("Incline Dumbbell Press" if has_dumbbell else "Pike Push-Ups"),
                "equipment_required": "barbell" if has_barbell else ("dumbbell" if has_dumbbell else "bodyweight"),
                "target_sets": main_sets,
                "target_rep_range_min": main_reps[0],
                "target_rep_range_max": main_reps[1],
                "prescribed_weight_kg": _prescribe_load("Overhead Barbell Press", 0.45 if has_barbell else 0.25),
                "target_rpe": 8.0,
                "rest_seconds": main_rest,
                "tempo": "2-0-1-0",
                "progression_rule": "Add 1.25-2.5 kg at top of rep range",
                "notes": "Primary vertical press."
            },
            {
                "exercise_name": "Lat Pulldown" if has_cables else "Pull-Ups / Chin-Ups",
                "equipment_required": "cables" if has_cables else "bodyweight",
                "target_sets": main_sets,
                "target_rep_range_min": 8,
                "target_rep_range_max": 12,
                "prescribed_weight_kg": _prescribe_load("Lat Pulldown", 0.55) if has_cables else 0.0,
                "target_rpe": 8.0,
                "rest_seconds": 120,
                "tempo": "2-0-1-1",
                "progression_rule": "Double progression in 8-12 rep zone",
                "notes": "Drive elbows down toward hips."
            },
            {
                "exercise_name": "Incline Dumbbell Press" if has_dumbbell else "Push-Ups",
                "equipment_required": "dumbbell" if has_dumbbell else "bodyweight",
                "target_sets": 3,
                "target_rep_range_min": acc_reps[0],
                "target_rep_range_max": acc_reps[1],
                "prescribed_weight_kg": _prescribe_load("Incline Dumbbell Press", 0.25),
                "target_rpe": 8.0,
                "rest_seconds": 90,
                "tempo": "2-1-1-0",
                "progression_rule": "Add 1-2 reps per session",
                "notes": "Upper clavicular pectoral focus."
            },
            {
                "exercise_name": "Dumbbell Lateral Raise" if has_dumbbell else "Pike Push-Ups",
                "equipment_required": "dumbbell" if has_dumbbell else "bodyweight",
                "target_sets": 3,
                "target_rep_range_min": 12,
                "target_rep_range_max": 15,
                "prescribed_weight_kg": _prescribe_load("Dumbbell Lateral Raise", 0.08),
                "target_rpe": 8.5,
                "rest_seconds": 60,
                "tempo": "2-0-1-1",
                "progression_rule": "Strict form medial delt isolation",
                "notes": "Lead with elbows."
            },
        ]

        lower_b = [
            {
                "exercise_name": "Conventional Barbell Deadlift" if has_barbell else ("Dumbbell Romanian Deadlift" if has_dumbbell else "Glute Bridge / Hip Thrust"),
                "equipment_required": "barbell" if has_barbell else ("dumbbell" if has_dumbbell else "bodyweight"),
                "target_sets": 3 if has_barbell else 4,
                "target_rep_range_min": main_reps[0],
                "target_rep_range_max": main_reps[1],
                "prescribed_weight_kg": _prescribe_load("Conventional Barbell Deadlift", 1.05 if has_barbell else 0.35),
                "target_rpe": 8.0,
                "rest_seconds": 180,
                "tempo": "2-1-1-0",
                "progression_rule": "Add 2.5-5.0 kg when all sets hit top rep target at <= RPE 8",
                "notes": "Primary posterior chain strength lift."
            },
            {
                "exercise_name": "Dumbbell Goblet Squat" if has_dumbbell else ("Leg Press" if has_cables else "Bodyweight Squat"),
                "equipment_required": "dumbbell" if has_dumbbell else ("machine" if has_cables else "bodyweight"),
                "target_sets": 3,
                "target_rep_range_min": 10,
                "target_rep_range_max": 12,
                "prescribed_weight_kg": _prescribe_load("Dumbbell Goblet Squat", 0.35),
                "target_rpe": 8.0,
                "rest_seconds": 90,
                "tempo": "2-1-1-0",
                "progression_rule": "Quad hypertrophy volume work",
                "notes": "Full knee flexion."
            },
            {
                "exercise_name": "Glute Bridge / Hip Thrust",
                "equipment_required": "bodyweight",
                "target_sets": 3,
                "target_rep_range_min": 12,
                "target_rep_range_max": 15,
                "prescribed_weight_kg": 0.0,
                "target_rpe": 8.0,
                "rest_seconds": 60,
                "tempo": "2-2-1-0",
                "progression_rule": "2-second glute squeeze at lockout",
                "notes": "Posterior pelvic tilt at lockout."
            },
        ]

        templates = [
            ("Upper Body A (Horizontal Focus)", "Chest, Upper Back, Arms", upper_a),
            ("Lower Body A (Squat Focus)", "Quadriceps, Hamstrings, Core", lower_a),
            ("Upper Body B (Vertical Focus)", "Shoulders, Lats, Upper Chest", upper_b),
            ("Lower Body B (Hinge Focus)", "Posterior Chain, Glutes, Quads", lower_b),
        ]

        days_out = []
        weekdays = preferred_days if len(preferred_days) >= days_per_week else ["Mon", "Tue", "Thu", "Fri", "Sat", "Sun", "Wed"]
        for idx in range(days_per_week):
            t_name, t_focus, ex_list = templates[idx % len(templates)]
            numbered_ex = []
            for order_i, ex_item in enumerate(ex_list, start=1):
                item_copy = dict(ex_item)
                item_copy["order_in_workout"] = order_i
                numbered_ex.append(item_copy)
            days_out.append({
                "day_number": idx + 1,
                "name": f"Day {idx + 1}: {t_name}",
                "target_focus": t_focus,
                "scheduled_weekday": weekdays[idx % len(weekdays)],
                "exercises": numbered_ex,
            })

        return {
            "plan_name": f"{goal.replace('_', ' ').title()} Periodized {days_per_week}-Day Program",
            "training_split": split_name,
            "duration_weeks": 4,
            "days_per_week": days_per_week,
            "days": days_out,
        }

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        context = envelope.context_data or {}
        provider = get_llm_provider()

        base_plan = self._build_deterministic_program(context)

        ai_resp = await provider.generate_structured_output(
            prompt=f"Generate workout plan for athlete context: {context}",
            system_instruction="You are an elite strength & conditioning coach.",
            response_schema=WorkoutPlanLLMOutput,
        )

        # If real LLM succeeded and returned populated days, use it after safety validation;
        # otherwise use the deterministic biomechanically balanced program.
        if not ai_resp.is_fallback and ai_resp.data.days:
            candidate_days = [d.model_dump() for d in ai_resp.data.days]
            plan_name = ai_resp.data.plan_name
            split_name = ai_resp.data.training_split
            explanation = ai_resp.data.explanation
        else:
            candidate_days = base_plan["days"]
            plan_name = base_plan["plan_name"]
            split_name = base_plan["training_split"]
            explanation = (
                f"Generated {base_plan['days_per_week']}-day '{plan_name}' using deterministic biomechanics "
                f"and RPE autoregulation rules tailored to available equipment "
                f"({', '.join(context.get('constraints', {}).get('equipment', ['bodyweight']))}). "
                + ("(Development Fallback Mode — No external LLM API key configured)" if ai_resp.is_fallback else "")
            )

        equipment_list = context.get("constraints", {}).get("equipment", ["bodyweight", "dumbbell", "barbell"])
        safety = validate_workout_plan_safety(candidate_days, equipment_list)

        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={
                "plan_name": plan_name,
                "training_split": split_name,
                "duration_weeks": 4,
                "days_per_week": len(candidate_days),
                "days": candidate_days,
                "safety_validation": safety,
            },
            explanation=explanation,
            validation_passed=safety["is_valid"],
            is_fallback=ai_resp.is_fallback,
        )
