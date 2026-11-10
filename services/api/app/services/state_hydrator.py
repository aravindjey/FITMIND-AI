"""Authoritative Athlete State Hydrator.
Retrieves current, persistent athlete context from the database without sending
unbounded history to LLM agents.
"""
from typing import Dict, Any, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.athlete import AthleteProfile, Goal
from app.models.nutrition import NutritionProfile, NutritionPlan, FoodLog
from app.models.workout import WorkoutPlan, WorkoutSession, PersonalRecord
from app.models.check_in import CheckIn
from app.models.progress import BodyMeasurement, ProgressPhoto
from app.models.audit import AgentAuditLog
from app.engines.weight_trend import calculate_ema_weight_trend, calculate_rate_of_change
from app.engines.workout_engine import calculate_recovery_readiness
from app.engines.nutrition_engine import calculate_nutrition_targets


class AthleteStateHydrator:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_hydrated_state(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Builds a structured, authoritative athlete context snapshot from PostgreSQL/SQLite."""
        prof_res = await self.session.execute(
            select(AthleteProfile)
            .options(selectinload(AthleteProfile.goals))
            .where(AthleteProfile.user_id == user_id)
            .execution_options(populate_existing=True)
        )
        profile = prof_res.scalars().first()
        if not profile:
            return {
                "has_profile": False,
                "user_id": str(user_id),
                "athlete_summary": None,
                "constraints": {},
                "nutrition_targets": None,
                "active_workout_plan": None,
                "active_nutrition_plan": None,
                "recent_weight_trend": {},
                "recent_recovery": {},
                "personal_records": [],
                "recent_sessions": [],
            }

        active_goal = next((g for g in profile.goals if g.is_active), profile.goals[0] if profile.goals else None)
        prefs = profile.training_preferences or {}

        # Nutrition Profile & Food Preferences
        nut_res = await self.session.execute(
            select(NutritionProfile)
            .options(selectinload(NutritionProfile.food_preferences))
            .where(NutritionProfile.athlete_profile_id == profile.id)
        )
        nut_profile = nut_res.scalars().first()

        food_prefs_by_type: Dict[str, List[str]] = {
            "staple": [],
            "liked": [],
            "disliked": [],
            "allergic": [],
            "avoided": [],
        }
        if nut_profile and nut_profile.food_preferences:
            for fp in nut_profile.food_preferences:
                bucket = fp.preference_type if fp.preference_type in food_prefs_by_type else "liked"
                food_prefs_by_type[bucket].append(fp.food_name)

        # Active Workout Plan
        wp_res = await self.session.execute(
            select(WorkoutPlan)
            .options(selectinload(WorkoutPlan.workout_days))
            .where(WorkoutPlan.athlete_profile_id == profile.id, WorkoutPlan.is_active == True)
            .order_by(WorkoutPlan.created_at.desc())
        )
        active_wp = wp_res.scalars().first()

        # Active Nutrition Plan
        active_np = None
        if nut_profile:
            np_res = await self.session.execute(
                select(NutritionPlan)
                .options(selectinload(NutritionPlan.meals))
                .where(NutritionPlan.nutrition_profile_id == nut_profile.id, NutritionPlan.is_active == True)
                .order_by(NutritionPlan.created_at.desc())
            )
            active_np = np_res.scalars().first()

        # Recent Check-ins (last 14 days)
        ci_res = await self.session.execute(
            select(CheckIn)
            .where(CheckIn.athlete_profile_id == profile.id)
            .order_by(CheckIn.check_in_date.desc())
            .limit(14)
        )
        recent_checkins = list(reversed(ci_res.scalars().all()))

        weights = [c.weight_kg for c in recent_checkins] if recent_checkins else [profile.current_weight_kg]
        ema_series = calculate_ema_weight_trend(weights)
        weekly_velocity = calculate_rate_of_change(weights)

        latest_checkin = recent_checkins[-1] if recent_checkins else None
        if latest_checkin:
            recovery_summary = calculate_recovery_readiness(
                sleep_hours=latest_checkin.sleep_hours or 7.5,
                sleep_quality_score=latest_checkin.sleep_quality_score or 7,
                energy_score=latest_checkin.energy_score or 7,
                soreness_score=latest_checkin.soreness_score or 3,
                stress_score=latest_checkin.stress_score or 4,
            )
        else:
            recovery_summary = {
                "readiness_score": 80,
                "status": "baseline_unlogged",
                "intensity_modifier": 1.0,
                "recommendation": "No daily check-ins logged yet; using baseline readiness.",
            }

        # Personal Records (top 10)
        pr_res = await self.session.execute(
            select(PersonalRecord)
            .where(PersonalRecord.athlete_profile_id == profile.id)
            .order_by(PersonalRecord.achieved_at.desc())
            .limit(10)
        )
        prs = pr_res.scalars().all()

        # Recent Workout Sessions (last 5)
        ws_res = await self.session.execute(
            select(WorkoutSession)
            .where(WorkoutSession.athlete_profile_id == profile.id)
            .order_by(WorkoutSession.started_at.desc())
            .limit(5)
        )
        sessions = ws_res.scalars().all()

        # Always compute authoritative deterministic nutrition targets & conflict warnings from current profile + goal
        det_targets = calculate_nutrition_targets(
            weight_kg=profile.current_weight_kg,
            height_cm=profile.height_cm,
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,
            primary_goal=active_goal.primary_goal if active_goal else "general_fitness",
            dietary_type=nut_profile.dietary_type if nut_profile else prefs.get("dietary_type", "omnivore"),
            target_weight_kg=active_goal.target_weight_kg if active_goal else None,
        )

        return {
            "has_profile": True,
            "user_id": str(user_id),
            "athlete_profile_id": str(profile.id),
            "athlete_summary": {
                "age": profile.age,
                "sex": profile.sex,
                "height_cm": profile.height_cm,
                "weight_kg": profile.current_weight_kg,
                "timezone": profile.timezone,
                "training_experience_years": profile.training_experience_years,
                "activity_level": profile.activity_level,
                "occupation_type": profile.occupation_type,
                "sport_name": profile.sport_name,
                "sport_position": profile.sport_position,
                "primary_goal": active_goal.primary_goal if active_goal else "general_fitness",
                "target_weight_kg": active_goal.target_weight_kg if active_goal else None,
                "goal_weight_conflict": det_targets["goal_weight_conflict"],
                "goal_conflict_warning": det_targets["goal_conflict_warning"],
            },
            "constraints": {
                "equipment": prefs.get("equipment", ["bodyweight", "dumbbell", "barbell"]),
                "days_per_week": prefs.get("days_per_week", 4),
                "preferred_days": prefs.get("preferred_days", ["Mon", "Tue", "Thu", "Fri"]),
                "session_duration_minutes": prefs.get("session_duration_minutes", 60),
                "dietary_type": nut_profile.dietary_type if nut_profile else prefs.get("dietary_type", "omnivore"),
                "weekly_budget_inr": nut_profile.weekly_food_budget_amount if nut_profile else prefs.get("weekly_budget_inr", 2500.0),
                "currency_code": nut_profile.currency_code if nut_profile else "INR",
                "meals_per_day": nut_profile.meals_per_day if nut_profile else 4,
                "allergies": food_prefs_by_type["allergic"],
                "disliked_foods": food_prefs_by_type["disliked"] + food_prefs_by_type["avoided"],
                "staple_foods": food_prefs_by_type["staple"] + food_prefs_by_type["liked"],
            },
            "nutrition_targets": det_targets,
            "active_workout_plan": {
                "id": str(active_wp.id),
                "name": active_wp.name,
                "training_split": active_wp.training_split,
                "days_per_week": active_wp.days_per_week,
                "day_count": len(active_wp.workout_days),
            } if active_wp else None,
            "active_nutrition_plan": {
                "id": str(active_np.id),
                "name": active_np.name,
                "daily_calories": active_np.daily_calories,
                "estimated_daily_cost_inr": active_np.estimated_daily_cost_inr,
                "meal_count": len(active_np.meals),
            } if active_np else None,
            "recent_weight_trend": {
                "current_weight_kg": profile.current_weight_kg,
                "ema_latest_kg": ema_series[-1] if ema_series else profile.current_weight_kg,
                "weekly_rate_kg": weekly_velocity,
                "data_points": len(recent_checkins),
            },
            "recent_recovery": recovery_summary,
            "personal_records": [
                {
                    "exercise_name": pr.exercise_name,
                    "weight_kg": pr.weight_kg,
                    "reps": pr.reps,
                    "estimated_1rm_kg": pr.estimated_1rm_kg,
                    "achieved_at": pr.achieved_at.isoformat(),
                }
                for pr in prs
            ],
            "recent_sessions": [
                {
                    "workout_name": s.workout_name,
                    "started_at": s.started_at.isoformat(),
                    "total_volume_kg": s.total_volume_kg,
                    "session_rpe": s.session_rpe,
                }
                for s in sessions
            ],
        }
