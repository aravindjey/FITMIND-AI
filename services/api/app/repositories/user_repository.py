from typing import Optional
import uuid
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models.athlete import AthleteProfile, Goal
from app.models.audit import AgentAuditLog
from app.models.check_in import CheckIn
from app.models.progress import BodyMeasurement, ProgressPhoto, Notification
from app.models.nutrition import NutritionProfile, FoodPreference, NutritionPlan, Meal, FoodLog
from app.models.workout import WorkoutPlan, WorkoutDay, WorkoutExercise, WorkoutSession, SetLog, PersonalRecord


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email.lower().strip()))
        return result.scalars().first()

    async def create(self, email: str, hashed_password: str, full_name: str) -> User:
        user = User(
            email=email.lower().strip(),
            hashed_password=hashed_password,
            full_name=full_name
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user_and_data(self, user: User) -> None:
        """Permanently deletes a user account and cascades erasure across all owned athlete records."""
        prof_res = await self.session.execute(
            select(AthleteProfile).where(AthleteProfile.user_id == user.id)
        )
        profile = prof_res.scalars().first()

        if profile:
            # Delete workout hierarchy
            wp_res = await self.session.execute(
                select(WorkoutPlan.id).where(WorkoutPlan.athlete_profile_id == profile.id)
            )
            wp_ids = [r[0] for r in wp_res.all()]
            if wp_ids:
                wd_res = await self.session.execute(
                    select(WorkoutDay.id).where(WorkoutDay.workout_plan_id.in_(wp_ids))
                )
                wd_ids = [r[0] for r in wd_res.all()]
                if wd_ids:
                    await self.session.execute(
                        delete(WorkoutExercise).where(WorkoutExercise.workout_day_id.in_(wd_ids))
                    )
                await self.session.execute(
                    delete(WorkoutDay).where(WorkoutDay.workout_plan_id.in_(wp_ids))
                )
            await self.session.execute(
                delete(WorkoutPlan).where(WorkoutPlan.athlete_profile_id == profile.id)
            )

            # Delete workout sessions & set logs
            ws_res = await self.session.execute(
                select(WorkoutSession.id).where(WorkoutSession.athlete_profile_id == profile.id)
            )
            ws_ids = [r[0] for r in ws_res.all()]
            if ws_ids:
                await self.session.execute(
                    delete(SetLog).where(SetLog.workout_session_id.in_(ws_ids))
                )
            await self.session.execute(
                delete(WorkoutSession).where(WorkoutSession.athlete_profile_id == profile.id)
            )
            await self.session.execute(
                delete(PersonalRecord).where(PersonalRecord.athlete_profile_id == profile.id)
            )

            # Delete nutrition hierarchy
            np_res = await self.session.execute(
                select(NutritionProfile.id).where(NutritionProfile.athlete_profile_id == profile.id)
            )
            np_ids = [r[0] for r in np_res.all()]
            if np_ids:
                nplan_res = await self.session.execute(
                    select(NutritionPlan.id).where(NutritionPlan.nutrition_profile_id.in_(np_ids))
                )
                nplan_ids = [r[0] for r in nplan_res.all()]
                if nplan_ids:
                    await self.session.execute(
                        delete(Meal).where(Meal.nutrition_plan_id.in_(nplan_ids))
                    )
                await self.session.execute(
                    delete(NutritionPlan).where(NutritionPlan.nutrition_profile_id.in_(np_ids))
                )
                await self.session.execute(
                    delete(FoodPreference).where(FoodPreference.nutrition_profile_id.in_(np_ids))
                )
                await self.session.execute(
                    delete(NutritionProfile).where(NutritionProfile.id.in_(np_ids))
                )

            await self.session.execute(
                delete(FoodLog).where(FoodLog.athlete_profile_id == profile.id)
            )
            await self.session.execute(
                delete(CheckIn).where(CheckIn.athlete_profile_id == profile.id)
            )
            await self.session.execute(
                delete(BodyMeasurement).where(BodyMeasurement.athlete_profile_id == profile.id)
            )
            await self.session.execute(
                delete(ProgressPhoto).where(ProgressPhoto.athlete_profile_id == profile.id)
            )
            await self.session.execute(
                delete(Goal).where(Goal.athlete_profile_id == profile.id)
            )
            await self.session.execute(
                delete(AthleteProfile).where(AthleteProfile.id == profile.id)
            )

        await self.session.execute(
            delete(Notification).where(Notification.user_id == user.id)
        )
        await self.session.execute(
            delete(AgentAuditLog).where(AgentAuditLog.user_id == user.id)
        )
        await self.session.delete(user)
        await self.session.commit()
