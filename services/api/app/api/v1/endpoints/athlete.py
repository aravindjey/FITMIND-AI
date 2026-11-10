from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.nutrition import NutritionProfile, FoodPreference
from app.models.progress import BodyMeasurement
from app.repositories.athlete_repository import AthleteRepository
from app.services.state_hydrator import AthleteStateHydrator
from app.engines.nutrition_engine import calculate_nutrition_targets
from app.schemas.athlete import (
    AthleteProfileCreate,
    AthleteProfileUpdate,
    AthleteProfileResponse,
    GoalSchema,
    OnboardingRequest,
)

router = APIRouter()


@router.post("/profile", response_model=AthleteProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_in: AthleteProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create athlete profile for current user."""
    repo = AthleteRepository(db)
    existing = await repo.get_by_user_id(current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Athlete profile already exists for this user. Use PUT to update."
        )

    profile_dict = profile_in.model_dump(exclude={"goal"})
    profile = await repo.create_profile(user_id=current_user.id, profile_data=profile_dict)

    if profile_in.goal:
        goal_dict = profile_in.goal.model_dump()
        await repo.create_or_update_goal(athlete_profile_id=profile.id, goal_data=goal_dict)
        await db.refresh(profile)

    return AthleteProfileResponse.model_validate(profile)


@router.get("/profile", response_model=AthleteProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch current user's athlete profile."""
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found for this user."
        )
    return AthleteProfileResponse.model_validate(profile)


@router.put("/profile", response_model=AthleteProfileResponse)
async def update_profile(
    profile_in: AthleteProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's athlete profile."""
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found for this user."
        )

    update_dict = profile_in.model_dump(exclude_unset=True, exclude={"goal"})
    profile = await repo.update_profile(user_id=current_user.id, update_data=update_dict)

    if profile_in.goal:
        goal_dict = profile_in.goal.model_dump(exclude_unset=True)
        await repo.create_or_update_goal(athlete_profile_id=profile.id, goal_data=goal_dict)
        await db.refresh(profile)

    # Synchronize NutritionProfile targets when profile or goal changes
    active_goal_obj = profile.goals[0] if getattr(profile, "goals", None) else None
    primary_goal = active_goal_obj.primary_goal if active_goal_obj else "general_fitness"
    target_weight_kg = active_goal_obj.target_weight_kg if active_goal_obj else None

    nut_res = await db.execute(
        select(NutritionProfile).where(NutritionProfile.athlete_profile_id == profile.id)
    )
    nut_profile = nut_res.scalars().first()
    if nut_profile:
        targets = calculate_nutrition_targets(
            weight_kg=profile.current_weight_kg,
            height_cm=profile.height_cm,
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,
            primary_goal=primary_goal,
            dietary_type=nut_profile.dietary_type or "omnivore",
            target_weight_kg=target_weight_kg,
        )
        nut_profile.bmr_kcal = targets["bmr_kcal"]
        nut_profile.tdee_kcal = targets["tdee_kcal"]
        nut_profile.target_calories = targets["target_calories"]
        nut_profile.protein_grams = targets["protein_grams"]
        nut_profile.carbs_grams = targets["carbs_grams"]
        nut_profile.fat_grams = targets["fat_grams"]
        await db.commit()
        await db.refresh(profile)

    return AthleteProfileResponse.model_validate(profile)


@router.post("/onboarding", status_code=status.HTTP_201_CREATED)
async def complete_onboarding(
    onboarding_in: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Completes comprehensive athlete onboarding: creates/updates AthleteProfile, Goal,
    deterministic NutritionProfile (BMR/TDEE/Macros), FoodPreferences, and initial weight log.
    """
    repo = AthleteRepository(db)
    existing = await repo.get_by_user_id(current_user.id)

    training_prefs = {
        "days_per_week": onboarding_in.days_per_week,
        "preferred_days": onboarding_in.preferred_days,
        "session_duration_minutes": onboarding_in.session_duration_minutes,
        "equipment": onboarding_in.available_equipment,
        "dietary_type": onboarding_in.dietary_type,
        "weekly_budget_inr": onboarding_in.weekly_food_budget_inr,
        "onboarding_completed": True,
    }

    profile_payload = {
        "age": onboarding_in.age,
        "sex": onboarding_in.sex,
        "height_cm": onboarding_in.height_cm,
        "current_weight_kg": onboarding_in.current_weight_kg,
        "timezone": onboarding_in.timezone,
        "training_experience_years": onboarding_in.training_experience_years,
        "activity_level": onboarding_in.activity_level,
        "occupation_type": onboarding_in.occupation_type,
        "sport_name": onboarding_in.sport_name,
        "sport_position": onboarding_in.sport_position,
        "training_preferences": training_prefs,
    }

    if existing:
        profile = await repo.update_profile(user_id=current_user.id, update_data=profile_payload)
    else:
        profile = await repo.create_profile(user_id=current_user.id, profile_data=profile_payload)

    await repo.create_or_update_goal(
        athlete_profile_id=profile.id,
        goal_data={
            "primary_goal": onboarding_in.primary_goal,
            "target_weight_kg": onboarding_in.target_weight_kg,
            "target_date": onboarding_in.target_date,
            "sport_name": onboarding_in.sport_name,
            "sport_position": onboarding_in.sport_position,
        }
    )

    # Calculate deterministic BMR, TDEE, and macronutrient targets
    targets = calculate_nutrition_targets(
        weight_kg=onboarding_in.current_weight_kg,
        height_cm=onboarding_in.height_cm,
        age=onboarding_in.age,
        sex=onboarding_in.sex,
        activity_level=onboarding_in.activity_level,
        primary_goal=onboarding_in.primary_goal,
        dietary_type=onboarding_in.dietary_type,
        target_weight_kg=onboarding_in.target_weight_kg,
    )

    nut_res = await db.execute(
        select(NutritionProfile).where(NutritionProfile.athlete_profile_id == profile.id)
    )
    nut_profile = nut_res.scalars().first()
    if not nut_profile:
        nut_profile = NutritionProfile(athlete_profile_id=profile.id)
        db.add(nut_profile)

    nut_profile.bmr_kcal = targets["bmr_kcal"]
    nut_profile.tdee_kcal = targets["tdee_kcal"]
    nut_profile.target_calories = targets["target_calories"]
    nut_profile.protein_grams = targets["protein_grams"]
    nut_profile.carbs_grams = targets["carbs_grams"]
    nut_profile.fat_grams = targets["fat_grams"]
    nut_profile.weekly_food_budget_amount = onboarding_in.weekly_food_budget_inr
    nut_profile.currency_code = onboarding_in.currency_code
    nut_profile.meals_per_day = onboarding_in.meals_per_day
    nut_profile.dietary_type = onboarding_in.dietary_type
    await db.flush()

    # Replace food preferences
    await db.execute(
        delete(FoodPreference).where(FoodPreference.nutrition_profile_id == nut_profile.id)
    )
    pref_buckets = [
        ("staple", onboarding_in.staple_foods),
        ("liked", onboarding_in.liked_foods),
        ("disliked", onboarding_in.disliked_foods),
        ("allergic", onboarding_in.allergies),
        ("avoided", onboarding_in.avoided_foods),
    ]
    for pref_type, items in pref_buckets:
        for item_name in items:
            cleaned = item_name.strip()
            if cleaned:
                db.add(FoodPreference(
                    nutrition_profile_id=nut_profile.id,
                    food_name=cleaned,
                    preference_type=pref_type,
                ))

    await db.commit()

    hydrator = AthleteStateHydrator(db)
    state = await hydrator.get_hydrated_state(current_user.id)
    return {
        "message": "Onboarding completed and persisted to database.",
        "nutrition_calculation_assumptions": targets["assumptions"],
        "hydrated_state": state,
    }


@router.get("/state")
async def get_hydrated_athlete_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns the authoritative hydrated athlete context from the database."""
    hydrator = AthleteStateHydrator(db)
    return await hydrator.get_hydrated_state(current_user.id)


@router.get("/weight-history")
async def get_weight_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns historical weight records from BodyMeasurement and CheckIn tables."""
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        return {"entries": []}

    bm_res = await db.execute(
        select(BodyMeasurement)
        .where(BodyMeasurement.athlete_profile_id == profile.id, BodyMeasurement.weight_kg != None)
        .order_by(BodyMeasurement.recorded_at.asc(), BodyMeasurement.created_at.asc())
    )
    measurements = bm_res.scalars().all()
    return {
        "current_weight_kg": profile.current_weight_kg,
        "entries": [
            {
                "id": str(m.id),
                "recorded_at": m.recorded_at.isoformat(),
                "weight_kg": m.weight_kg,
                "notes": m.notes,
                "created_at": m.created_at.isoformat(),
            }
            for m in measurements
        ]
    }
