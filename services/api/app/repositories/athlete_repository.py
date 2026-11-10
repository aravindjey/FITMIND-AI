from typing import Optional, Dict, Any
import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.athlete import AthleteProfile, Goal
from app.models.progress import BodyMeasurement


class AthleteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[AthleteProfile]:
        """Fetch athlete profile for a specific user ID enforcing tenant boundary."""
        result = await self.session.execute(
            select(AthleteProfile)
            .options(selectinload(AthleteProfile.goals))
            .where(AthleteProfile.user_id == user_id)
        )
        return result.scalars().first()

    async def create_profile(self, user_id: uuid.UUID, profile_data: Dict[str, Any]) -> AthleteProfile:
        """Create athlete profile for user and record initial historical weight entry."""
        profile = AthleteProfile(
            user_id=user_id,
            age=profile_data["age"],
            sex=profile_data["sex"],
            height_cm=profile_data["height_cm"],
            current_weight_kg=profile_data["current_weight_kg"],
            timezone=profile_data.get("timezone", "UTC"),
            training_experience_years=profile_data.get("training_experience_years", 0.0),
            activity_level=profile_data["activity_level"],
            occupation_type=profile_data.get("occupation_type"),
            sport_name=profile_data.get("sport_name"),
            sport_position=profile_data.get("sport_position"),
            training_preferences=profile_data.get("training_preferences", {})
        )
        self.session.add(profile)
        await self.session.flush()

        # Record initial historical weight snapshot
        initial_measurement = BodyMeasurement(
            athlete_profile_id=profile.id,
            recorded_at=date.today(),
            weight_kg=float(profile.current_weight_kg),
            notes="Initial profile weight baseline"
        )
        self.session.add(initial_measurement)

        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def update_profile(self, user_id: uuid.UUID, update_data: Dict[str, Any]) -> Optional[AthleteProfile]:
        """Update existing athlete profile for user and preserve historical weight changes."""
        profile = await self.get_by_user_id(user_id)
        if not profile:
            return None

        old_weight = profile.current_weight_kg
        new_weight = update_data.get("current_weight_kg")

        for key, value in update_data.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)

        if new_weight is not None and float(new_weight) != float(old_weight):
            weight_log = BodyMeasurement(
                athlete_profile_id=profile.id,
                recorded_at=date.today(),
                weight_kg=float(new_weight),
                notes=f"Profile weight updated from {old_weight} kg to {new_weight} kg"
            )
            self.session.add(weight_log)

        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def create_or_update_goal(self, athlete_profile_id: uuid.UUID, goal_data: Dict[str, Any]) -> Goal:
        """Create or update primary goal for athlete profile."""
        result = await self.session.execute(
            select(Goal).where(
                Goal.athlete_profile_id == athlete_profile_id,
                Goal.is_active == True
            )
        )
        goal = result.scalars().first()
        if not goal:
            goal = Goal(athlete_profile_id=athlete_profile_id)

        goal.primary_goal = goal_data["primary_goal"]
        goal.target_weight_kg = goal_data.get("target_weight_kg")
        goal.target_date = goal_data.get("target_date")
        goal.sport_name = goal_data.get("sport_name")
        goal.sport_position = goal_data.get("sport_position")

        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal
