from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.athlete_repository import AthleteRepository
from app.schemas.athlete import (
    AthleteProfileCreate,
    AthleteProfileUpdate,
    AthleteProfileResponse,
    GoalSchema
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

    return AthleteProfileResponse.model_validate(profile)
