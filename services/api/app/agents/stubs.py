from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentInputEnvelope, AgentOutputEnvelope
from app.ai.factory import get_llm_provider, get_vision_provider
from app.engines.workout_engine import calculate_recovery_readiness
from app.engines.safety_engine import validate_nutrition_plan_safety, validate_workout_plan_safety


class CoachingResponseSchema(BaseModel):
    answer: str = "Based on your authoritative athlete profile and training history, prioritize progressive overload and hitting your daily protein target."
    actionable_steps: List[str] = Field(default_factory=lambda: [
        "Complete all prescribed compound working sets at target RPE 8.",
        "Hit your daily protein and calorie target consistently.",
        "Log your daily check-in weight and sleep duration."
    ])
    referenced_metrics: List[str] = Field(default_factory=list)


class VisualBodyAnalysisSchema(BaseModel):
    posture_observations: List[str] = Field(default_factory=lambda: [
        "Neutral standing alignment observed; keep shoulders relaxed during front/side comparisons."
    ])
    muscular_development_notes: List[str] = Field(default_factory=lambda: [
        "Upper torso and shoulder frame establish a solid baseline for progressive hypertrophy tracking."
    ])
    symmetry_notes: List[str] = Field(default_factory=lambda: [
        "Balanced bilateral proportion; continue including unilateral movements (split squats, single-arm rows)."
    ])
    qualitative_body_composition_range: str = "Estimated ~14% - 19% visual range (Qualitative Visual Indicator Only)"
    confidence_level: str = "moderate_qualitative"
    uncertainty_disclaimer: str = (
        "IMPORTANT UNCERTAINTY NOTICE: Visual photograph analysis is a qualitative indicator affected by lighting, "
        "hydration, camera focal length, and posture. It is NOT a clinical or medical DEXA body-fat measurement."
    )


class FitnessCoachingAgent(BaseAgent):
    """Component #4: Fitness Coaching Agent.
    Answers natural-language fitness, training, and nutrition questions grounded in the
    athlete's hydrated database context.
    """

    @property
    def agent_name(self) -> str:
        return "FitnessCoachingAgent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        context = envelope.context_data or {}
        prompt_text = (envelope.user_prompt or "").strip()
        summary = context.get("athlete_summary") or {}
        nut_targets = context.get("nutrition_targets") or {}
        recovery = context.get("recent_recovery") or {}
        weight_trend = context.get("recent_weight_trend") or {}
        constraints = context.get("constraints") or {}

        provider = get_llm_provider()
        ai_resp = await provider.generate_structured_output(
            prompt=f"Athlete Context: {context}\n\nAthlete Question: {prompt_text}",
            system_instruction=(
                "You are an evidence-based strength & conditioning coach and sports nutritionist. "
                "Use ONLY the provided database athlete facts; never invent athlete history."
            ),
            response_schema=CoachingResponseSchema,
        )

        weight = summary.get("weight_kg", "unrecorded")
        target_weight = summary.get("target_weight_kg")
        goal = str(summary.get("primary_goal", "general_fitness")).replace("_", " ")
        goal_conflict_warning = summary.get("goal_conflict_warning") or nut_targets.get("goal_conflict_warning")
        cal = nut_targets.get("target_calories", "not yet calculated")
        pro = nut_targets.get("protein_grams", "not yet calculated")
        readiness = recovery.get("readiness_score", 80)
        weekly_rate = weight_trend.get("weekly_rate_kg", 0.0)
        active_wp = context.get("active_workout_plan")
        active_np = context.get("active_nutrition_plan")

        if active_wp:
            workout_status_text = (
                f"your active {active_wp.get('days_per_week', 4)}-day '{active_wp.get('name')}' "
                f"({str(active_wp.get('training_split', 'split')).replace('_', ' ')})"
            )
            workout_ref_label = f"Active Workout Plan: {active_wp.get('name')} ({active_wp.get('days_per_week')}d/wk)"
        else:
            workout_status_text = (
                f"no active workout plan generated yet (your profile preference is {constraints.get('days_per_week', 4)} days/week; "
                f"visit the Workout Planner to generate your active program)"
            )
            workout_ref_label = "Active Workout Plan: None (Not Yet Generated)"

        if not ai_resp.is_fallback and ai_resp.data.answer:
            answer = ai_resp.data.answer
            steps = ai_resp.data.actionable_steps
        else:
            q_lower = prompt_text.lower()
            if any(w in q_lower for w in ("diet", "food", "protein", "calorie", "eat", "meal", "paneer", "budget")):
                answer = (
                    f"Based on your current database profile ({weight} kg"
                    + (f", target weight: {target_weight} kg" if target_weight else "")
                    + f", primary goal: {goal}), "
                    f"your deterministic nutrition targets are {cal} kcal/day with {pro}g protein. "
                    f"Your configured diet type is '{constraints.get('dietary_type', 'omnivore')}' with a weekly food budget of ₹{constraints.get('weekly_budget_inr', 2500)}. "
                    f"Distribute protein evenly across {constraints.get('meals_per_day', 4)} meals using your preferred staples."
                )
                steps = [
                    f"Target {cal} kcal and {pro}g protein daily across {constraints.get('meals_per_day', 4)} meals.",
                    "Weigh staple grains and protein sources consistently (raw vs cooked).",
                    "Use the Nutrition Planner to generate or swap INR budget-matched meals.",
                ]
            elif any(w in q_lower for w in ("sleep", "tired", "sore", "recovery", "fatigue", "deload", "rest")):
                answer = (
                    f"Your current recovery readiness score is {readiness}/100 ({recovery.get('status', 'moderate')}). "
                    f"{recovery.get('recommendation', 'Prioritize 7.5-8.5 hours of sleep and cap sets at RPE 8.')}"
                )
                steps = [
                    f"Apply today's intensity modifier ({recovery.get('intensity_modifier', 1.0) * 100:.0f}% of normal working load).",
                    "Aim for >= 7.5 hours of sleep and 3.0+ liters of hydration today.",
                    "Log your daily check-in tomorrow morning to update your readiness trend.",
                ]
            else:
                if active_wp:
                    answer = (
                        f"For your primary goal of {goal} at {weight} kg (7-day weight velocity: {weekly_rate:+.2f} kg/week, "
                        f"readiness: {readiness}/100), focus on progressive overload within {workout_status_text} "
                        f"while maintaining {cal} kcal and {pro}g protein/day."
                    )
                    steps = [
                        f"Follow {active_wp.get('name')} and log every working set with weight, reps, and RPE.",
                        "When you hit the top of your target rep range at <= RPE 8, increase load by 2.5 kg next session.",
                        f"Maintain daily intake around {cal} kcal and {pro}g protein.",
                    ]
                else:
                    answer = (
                        f"For your primary goal of {goal} at {weight} kg (7-day weight velocity: {weekly_rate:+.2f} kg/week, "
                        f"readiness: {readiness}/100), you currently have {workout_status_text}. "
                        f"Your daily nutrition target is {cal} kcal and {pro}g protein/day."
                    )
                    steps = [
                        "Open the Workout Planner and click 'Generate AI Workout Plan' to create your active training split.",
                        "Once generated, log every working set with weight, reps, and RPE to track progressive overload.",
                        f"Maintain daily intake around {cal} kcal and {pro}g protein.",
                    ]

            if goal_conflict_warning:
                answer = f"⚠️ {goal_conflict_warning}\n\n{answer}"
                steps.insert(0, "Review your Primary Goal vs. Target Weight in Athlete Profile so they align.")

        referenced = [
            f"Weight: {weight} kg" + (f" -> Target: {target_weight} kg" if target_weight else ""),
            f"Goal: {goal}",
            f"Target Calories: {cal} kcal ({pro}g Protein)",
            workout_ref_label,
            f"Readiness Score: {readiness}/100",
        ]

        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={
                "answer": answer,
                "actionable_steps": steps,
                "referenced_metrics": referenced,
            },
            explanation=answer + (" [Development Fallback Mode]" if ai_resp.is_fallback else ""),
            validation_passed=True,
            is_fallback=ai_resp.is_fallback,
        )


class ProgressAgent(BaseAgent):
    """Component #5: Progress Analysis Agent.
    Analyzes body-weight EMA trends, measurement changes, and strength PR progression.
    """

    @property
    def agent_name(self) -> str:
        return "ProgressAgent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        context = envelope.context_data or {}
        summary = context.get("athlete_summary") or {}
        trend = context.get("recent_weight_trend") or {}
        prs = context.get("personal_records") or []
        sessions = context.get("recent_sessions") or []

        goal = summary.get("primary_goal", "general_fitness")
        weekly_rate = float(trend.get("weekly_rate_kg", 0.0))
        ema_weight = trend.get("ema_latest_kg", summary.get("weight_kg", 70.0))

        if goal == "fat_loss":
            if -0.85 <= weekly_rate <= -0.25:
                trajectory = "on_track"
                insight = f"Weight trend ({weekly_rate:+.2f} kg/week) is in the optimal fat-loss zone (0.25-0.85 kg/week loss)."
            elif weekly_rate > -0.15:
                trajectory = "plateau_detected"
                insight = f"Weight velocity ({weekly_rate:+.2f} kg/week) indicates a plateau. Consider a -150 kcal adjustment or +1,500 daily steps."
            else:
                trajectory = " losing_too_fast"
                insight = f"Weight loss rate ({weekly_rate:+.2f} kg/week) is rapid; increase calories by +150-200 kcal to preserve lean muscle mass."
        elif goal in ("muscle_gain", "bodybuilding", "strength", "powerlifting"):
            if 0.10 <= weekly_rate <= 0.45:
                trajectory = "on_track"
                insight = f"Lean mass gain velocity ({weekly_rate:+.2f} kg/week) is right on target."
            elif weekly_rate < 0.05:
                trajectory = "under_gaining"
                insight = f"Weight trend ({weekly_rate:+.2f} kg/week) is flat; add +150 kcal/day from complex carbohydrates."
            else:
                trajectory = "surplus_high"
                insight = f"Weight gain velocity ({weekly_rate:+.2f} kg/week) is slightly elevated; trim surplus by ~150 kcal."
        else:
            trajectory = "stable"
            insight = f"7-day smoothed EMA weight is {ema_weight} kg ({weekly_rate:+.2f} kg/week)."

        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={
                "ema_weight_kg": ema_weight,
                "weekly_rate_kg": weekly_rate,
                "trajectory_status": trajectory,
                "pr_count": len(prs),
                "recent_session_count": len(sessions),
                "insight": insight,
            },
            explanation=insight,
            validation_passed=True,
            is_fallback=False,
        )


class RecoveryAgent(BaseAgent):
    """Component #6: Recovery Agent.
    Evaluates sleep, fatigue, soreness, and stress to compute readiness and training adjustments.
    """

    @property
    def agent_name(self) -> str:
        return "RecoveryAgent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        context = envelope.context_data or {}
        rec_input = context.get("check_in_metrics") or context.get("recent_recovery") or {}

        if "readiness_score" in rec_input and "sleep_hours" not in rec_input:
            assessment = {
                "readiness_score": rec_input.get("readiness_score", 80),
                "status": rec_input.get("status", "optimal"),
                "intensity_modifier": rec_input.get("intensity_modifier", 1.0),
                "recommendation": rec_input.get(
                    "recommendation",
                    "Readiness assessed from recent recovery log; proceed with prescribed working sets.",
                ),
            }
        else:
            assessment = calculate_recovery_readiness(
                sleep_hours=float(rec_input.get("sleep_hours", 7.5)),
                sleep_quality_score=int(rec_input.get("sleep_quality_score", 7)),
                energy_score=int(rec_input.get("energy_score", 7)),
                soreness_score=int(rec_input.get("soreness_score", 3)),
                stress_score=int(rec_input.get("stress_score", 4)),
            )

        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data=assessment,
            explanation=assessment["recommendation"],
            validation_passed=True,
            is_fallback=False,
        )


class BodyAnalysisAgent(BaseAgent):
    """Component #1: Body Analysis Agent.
    Analyzes uploaded progress photographs through BaseVisionProvider and compares measurements
    with explicit estimation uncertainty.
    """

    @property
    def agent_name(self) -> str:
        return "BodyAnalysisAgent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        context = envelope.context_data or {}
        image_bytes: bytes = context.get("image_bytes", b"")
        photo_type = context.get("photo_type", "front")
        weight_kg = context.get("weight_kg")
        previous_weight_kg = context.get("previous_weight_kg")

        vision_provider = get_vision_provider()
        vision_resp = await vision_provider.analyze_image_structured(
            image_bytes=image_bytes or b"placeholder",
            prompt=(
                f"Analyze athlete {photo_type} progress photograph. Provide qualitative posture, muscular "
                f"development, and symmetry observations with explicit estimation uncertainty. Never claim exact body fat %."
            ),
            response_schema=VisualBodyAnalysisSchema,
        )

        analysis_dict = vision_resp.data.model_dump()
        if weight_kg and previous_weight_kg:
            delta = round(float(weight_kg) - float(previous_weight_kg), 2)
            analysis_dict["weight_comparison_note"] = (
                f"Body weight changed by {delta:+.2f} kg since previous comparison ({previous_weight_kg} kg -> {weight_kg} kg)."
            )
        else:
            analysis_dict["weight_comparison_note"] = "Baseline visual record logged for longitudinal comparison."

        analysis_dict["is_fallback"] = vision_resp.is_fallback
        if vision_resp.is_fallback:
            analysis_dict["provider_notice"] = (
                "Vision API credentials not configured — returning structured baseline guidance with explicit uncertainty."
            )

        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data=analysis_dict,
            explanation=analysis_dict["uncertainty_disclaimer"],
            validation_passed=True,
            is_fallback=vision_resp.is_fallback,
        )


class SafetyValidationComponent(BaseAgent):
    """Component #7: Safety & Validation Agent.
    Validates workout and nutrition recommendations against configurable safety thresholds.
    """

    @property
    def agent_name(self) -> str:
        return "SafetyValidationComponent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        context = envelope.context_data or {}
        violations: List[str] = []
        warnings: List[str] = []

        if "nutrition_plan" in context:
            np_data = context["nutrition_plan"]
            targets = np_data.get("targets") or {}
            res = validate_nutrition_plan_safety(
                target_calories=int(targets.get("target_calories", 2000)),
                bmr_kcal=int(targets.get("bmr_kcal", 1500)),
                tdee_kcal=int(targets.get("tdee_kcal", 2200)),
                allergies=context.get("allergies", []),
                meals=np_data.get("meals", []),
            )
            violations.extend(res["violations"])
            warnings.extend(res["warnings"])

        if "workout_plan" in context:
            wp_data = context["workout_plan"]
            res = validate_workout_plan_safety(
                workout_days=wp_data.get("days", []),
                available_equipment=context.get("equipment", ["bodyweight"]),
            )
            violations.extend(res["violations"])
            warnings.extend(res["warnings"])

        passed = len(violations) == 0
        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={
                "is_valid": passed,
                "violations": violations,
                "warnings": warnings,
            },
            explanation="Safety validation passed." if passed else f"Validation failed: {'; '.join(violations)}",
            validation_passed=passed,
            is_fallback=False,
        )


class LifestyleHabitAgent(BaseAgent):
    """Component #8: Lifestyle & Habit Agent.
    Evaluates daily check-in consistency, hydration, sleep habits, and reminder schedules.
    """

    @property
    def agent_name(self) -> str:
        return "LifestyleHabitAgent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        context = envelope.context_data or {}
        checkin = context.get("latest_check_in") or {}
        streak_days = int(context.get("checkin_streak_days", 1))
        hydration = float(checkin.get("hydration_liters") or 2.5)
        sleep_hours = float(checkin.get("sleep_hours") or 7.5)
        adherence = int(checkin.get("nutrition_adherence_percent") or 85)

        habit_tips: List[str] = []
        if hydration < 3.0:
            habit_tips.append(f"Hydration logged at {hydration}L — aim for 3.0-3.5L/day (add 500ml upon waking and around training).")
        else:
            habit_tips.append(f"Hydration target met ({hydration}L).")

        if sleep_hours < 7.0:
            habit_tips.append(f"Sleep duration ({sleep_hours}h) is below optimal recovery threshold (7.5h+); set a wind-down reminder 45 mins before bed.")
        else:
            habit_tips.append(f"Sleep duration ({sleep_hours}h) supports muscular and neural recovery.")

        if adherence < 80:
            habit_tips.append(f"Nutrition adherence ({adherence}%) dipped; prep staple proteins in advance to simplify weekday meals.")

        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={
                "checkin_streak_days": streak_days,
                "habit_recommendations": habit_tips,
                "suggested_reminders": [
                    {"title": "Morning Weigh-In & Hydration", "scheduled_time": "07:30", "notification_type": "check_in"},
                    {"title": "Training Session Readiness", "scheduled_time": "17:30", "notification_type": "workout"},
                    {"title": "High-Protein Dinner & Sleep Wind-Down", "scheduled_time": "21:30", "notification_type": "recovery"},
                ],
            },
            explanation=" | ".join(habit_tips),
            validation_passed=True,
            is_fallback=False,
        )
