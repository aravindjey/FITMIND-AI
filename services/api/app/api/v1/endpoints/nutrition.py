from typing import List, Optional, Dict, Any
from datetime import date
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.nutrition import (
    NutritionProfile,
    FoodPreference,
    FoodItem,
    NutritionPlan,
    Meal,
    FoodLog,
)
from app.repositories.athlete_repository import AthleteRepository
from app.repositories.audit_repository import AuditRepository
from app.services.seed_data import ensure_seed_data
from app.services.state_hydrator import AthleteStateHydrator
from app.agents.base import AgentInputEnvelope, AgentRunner
from app.agents.nutrition_agent import NutritionAgent
from app.engines.nutrition_engine import calculate_nutrition_targets

router = APIRouter()


class FoodLogCreateRequest(BaseModel):
    food_item_id: Optional[uuid.UUID] = None
    food_name: str
    meal_type: str = "lunch"  # breakfast | lunch | snack | pre_workout | post_workout | dinner
    preparation_state: str = "cooked"  # raw | cooked | ready_to_eat
    quantity_grams: float = Field(..., gt=0, le=5000)
    log_date: Optional[str] = None  # YYYY-MM-DD


@router.get("/targets")
async def get_nutrition_targets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns deterministic BMR, TDEE, and macronutrient targets for the current athlete."""
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found. Complete profile or onboarding first."
        )

    active_goal = next((g for g in profile.goals if g.is_active), profile.goals[0] if profile.goals else None)
    goal = active_goal.primary_goal if active_goal else "general_fitness"
    target_weight_kg = active_goal.target_weight_kg if active_goal else None
    prefs = profile.training_preferences or {}
    dietary_type = prefs.get("dietary_type", "omnivore")

    nut_res = await db.execute(
        select(NutritionProfile)
        .options(selectinload(NutritionProfile.food_preferences))
        .where(NutritionProfile.athlete_profile_id == profile.id)
    )
    nut_profile = nut_res.scalars().first()
    effective_diet = nut_profile.dietary_type if nut_profile else dietary_type

    targets = calculate_nutrition_targets(
        weight_kg=profile.current_weight_kg,
        height_cm=profile.height_cm,
        age=profile.age,
        sex=profile.sex,
        activity_level=profile.activity_level,
        primary_goal=goal,
        dietary_type=effective_diet,
        target_weight_kg=target_weight_kg,
    )

    return {
        **targets,
        "current_weight_kg": profile.current_weight_kg,
        "target_weight_kg": target_weight_kg,
        "primary_goal": goal,
        "dietary_type": effective_diet,
        "weekly_food_budget_inr": nut_profile.weekly_food_budget_amount if nut_profile else prefs.get("weekly_budget_inr", 2500.0),
        "currency_code": nut_profile.currency_code if nut_profile else "INR",
        "meals_per_day": nut_profile.meals_per_day if nut_profile else 4,
    }


@router.get("/foods")
async def list_validated_foods(
    category: Optional[str] = None,
    vegetarian_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns validated Indian & global food items with exact per-100g nutritional data and INR costs."""
    await ensure_seed_data(db)
    query = select(FoodItem).order_by(FoodItem.category, FoodItem.name)
    if category:
        query = query.where(FoodItem.category == category.lower().strip())
    if vegetarian_only:
        query = query.where(FoodItem.is_vegetarian == True)

    res = await db.execute(query)
    items = res.scalars().all()
    return [
        {
            "id": str(f.id),
            "name": f.name,
            "category": f.category,
            "preparation_state": f.preparation_state,
            "serving_unit": f.serving_unit,
            "serving_grams": f.serving_grams,
            "calories_per_100g": f.calories_per_100g,
            "protein_per_100g": f.protein_per_100g,
            "carbs_per_100g": f.carbs_per_100g,
            "fat_per_100g": f.fat_per_100g,
            "fiber_per_100g": f.fiber_per_100g,
            "estimated_cost_inr_per_100g": f.estimated_cost_inr_per_100g,
            "is_vegetarian": f.is_vegetarian,
            "is_vegan": f.is_vegan,
            "is_indian_staple": f.is_indian_staple,
        }
        for f in items
    ]


@router.post("/generate-plan", status_code=status.HTTP_201_CREATED)
async def generate_nutrition_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates, validates, and persists an INR-budget-aware personalized meal plan."""
    await ensure_seed_data(db)
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete your athlete profile or onboarding before generating a nutrition plan."
        )

    hydrator = AthleteStateHydrator(db)
    state = await hydrator.get_hydrated_state(current_user.id)

    agent = NutritionAgent()
    runner = AgentRunner(audit_repo=AuditRepository(db))
    envelope = AgentInputEnvelope(
        user_id=current_user.id,
        action="generate_nutrition",
        context_data=state,
        user_prompt="Generate personalized INR budget-aware nutrition plan",
    )
    output = await runner.run_agent(agent, envelope)
    if not output.validation_passed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Nutrition plan failed safety validation: {output.result_data.get('safety_validation')}"
        )

    res_data = output.result_data
    targets = res_data["targets"]

    # Ensure NutritionProfile exists
    np_res = await db.execute(
        select(NutritionProfile).where(NutritionProfile.athlete_profile_id == profile.id)
    )
    nut_profile = np_res.scalars().first()
    if not nut_profile:
        nut_profile = NutritionProfile(
            athlete_profile_id=profile.id,
            bmr_kcal=targets["bmr_kcal"],
            tdee_kcal=targets["tdee_kcal"],
            target_calories=targets["target_calories"],
            protein_grams=targets["protein_grams"],
            carbs_grams=targets["carbs_grams"],
            fat_grams=targets["fat_grams"],
            weekly_food_budget_amount=state.get("constraints", {}).get("weekly_budget_inr", 2500.0),
            currency_code="INR",
            meals_per_day=state.get("constraints", {}).get("meals_per_day", 4),
            dietary_type=state.get("constraints", {}).get("dietary_type", "omnivore"),
        )
        db.add(nut_profile)
        await db.flush()
    else:
        nut_profile.bmr_kcal = targets["bmr_kcal"]
        nut_profile.tdee_kcal = targets["tdee_kcal"]
        nut_profile.target_calories = targets["target_calories"]
        nut_profile.protein_grams = targets["protein_grams"]
        nut_profile.carbs_grams = targets["carbs_grams"]
        nut_profile.fat_grams = targets["fat_grams"]

    # Deactivate old plans
    old_plans = await db.execute(
        select(NutritionPlan).where(
            NutritionPlan.nutrition_profile_id == nut_profile.id,
            NutritionPlan.is_active == True,
        )
    )
    for op_item in old_plans.scalars().all():
        op_item.is_active = False

    new_plan = NutritionPlan(
        nutrition_profile_id=nut_profile.id,
        name=res_data["plan_name"],
        daily_calories=targets["target_calories"],
        protein_grams=targets["protein_grams"],
        carbs_grams=targets["carbs_grams"],
        fat_grams=targets["fat_grams"],
        estimated_daily_cost_inr=res_data.get("estimated_daily_cost_inr", 0.0),
        calculation_assumptions=targets.get("assumptions"),
        is_active=True,
        is_fallback=output.is_fallback,
    )
    db.add(new_plan)
    await db.flush()

    for m_data in res_data.get("meals", []):
        meal_obj = Meal(
            nutrition_plan_id=new_plan.id,
            meal_number=m_data["meal_number"],
            name=m_data["name"],
            time_of_day=m_data.get("time_of_day"),
            target_calories=m_data["target_calories"],
            protein_g=m_data["protein_g"],
            carbs_g=m_data["carbs_g"],
            fat_g=m_data["fat_g"],
            estimated_cost_inr=m_data.get("estimated_cost_inr", 0.0),
            recipe_instructions=m_data.get("recipe_instructions"),
            ingredients=m_data.get("ingredients", []),
        )
        db.add(meal_obj)

    await db.commit()
    return await get_active_nutrition_plan(current_user=current_user, db=db)


@router.get("/active-plan")
async def get_active_nutrition_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves the current active nutrition plan and meal breakdown."""
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        return {"has_active_plan": False, "plan": None}

    np_res = await db.execute(
        select(NutritionProfile).where(NutritionProfile.athlete_profile_id == profile.id)
    )
    nut_profile = np_res.scalars().first()
    if not nut_profile:
        return {"has_active_plan": False, "plan": None}

    plan_res = await db.execute(
        select(NutritionPlan)
        .options(selectinload(NutritionPlan.meals))
        .where(NutritionPlan.nutrition_profile_id == nut_profile.id, NutritionPlan.is_active == True)
        .order_by(NutritionPlan.created_at.desc())
    )
    plan = plan_res.scalars().first()
    if not plan:
        return {"has_active_plan": False, "plan": None}

    return {
        "has_active_plan": True,
        "plan": {
            "id": str(plan.id),
            "name": plan.name,
            "daily_calories": plan.daily_calories,
            "protein_grams": plan.protein_grams,
            "carbs_grams": plan.carbs_grams,
            "fat_grams": plan.fat_grams,
            "estimated_daily_cost_inr": plan.estimated_daily_cost_inr,
            "estimated_weekly_cost_inr": round((plan.estimated_daily_cost_inr or 0.0) * 7.0, 2),
            "weekly_budget_inr": nut_profile.weekly_food_budget_amount,
            "currency_code": nut_profile.currency_code,
            "dietary_type": nut_profile.dietary_type,
            "calculation_assumptions": plan.calculation_assumptions,
            "is_fallback": plan.is_fallback,
            "meals": [
                {
                    "id": str(m.id),
                    "meal_number": m.meal_number,
                    "name": m.name,
                    "time_of_day": m.time_of_day,
                    "target_calories": m.target_calories,
                    "protein_g": m.protein_g,
                    "carbs_g": m.carbs_g,
                    "fat_g": m.fat_g,
                    "estimated_cost_inr": m.estimated_cost_inr,
                    "recipe_instructions": m.recipe_instructions,
                    "ingredients": m.ingredients,
                }
                for m in plan.meals
            ],
        },
    }


@router.post("/logs", status_code=status.HTTP_201_CREATED)
async def log_food_intake(
    log_in: FoodLogCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logs food intake using validated database nutritional values (never LLM-invented macros).
    Handles raw-to-cooked state conversion when needed.
    """
    await ensure_seed_data(db)
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Athlete profile required before logging food."
        )

    food_item = None
    if log_in.food_item_id:
        f_res = await db.execute(select(FoodItem).where(FoodItem.id == log_in.food_item_id))
        food_item = f_res.scalars().first()
    if not food_item:
        f_res = await db.execute(
            select(FoodItem).where(FoodItem.name.ilike(f"%{log_in.food_name.strip()}%"))
        )
        food_item = f_res.scalars().first()

    if not food_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food item '{log_in.food_name}' not found in validated nutritional database."
        )

    # Calculate exact nutritional totals from validated per-100g database record
    multiplier = log_in.quantity_grams / 100.0
    # If item in DB is raw grain/pulse but user logged cooked weight (or vice versa), adjust density factor explicitly
    if food_item.preparation_state == "raw" and log_in.preparation_state == "cooked" and food_item.category in ("grain", "pulse_dal"):
        multiplier = (log_in.quantity_grams / 2.8) / 100.0

    calories = round(food_item.calories_per_100g * multiplier, 1)
    protein_g = round(food_item.protein_per_100g * multiplier, 1)
    carbs_g = round(food_item.carbs_per_100g * multiplier, 1)
    fat_g = round(food_item.fat_per_100g * multiplier, 1)
    cost_inr = round(food_item.estimated_cost_inr_per_100g * multiplier, 2)

    parsed_date = date.fromisoformat(log_in.log_date) if log_in.log_date else date.today()

    entry = FoodLog(
        athlete_profile_id=profile.id,
        food_item_id=food_item.id,
        log_date=parsed_date,
        meal_type=log_in.meal_type,
        food_name=food_item.name,
        preparation_state=log_in.preparation_state,
        quantity_grams=log_in.quantity_grams,
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        cost_inr=cost_inr,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return {
        "id": str(entry.id),
        "log_date": entry.log_date.isoformat(),
        "meal_type": entry.meal_type,
        "food_name": entry.food_name,
        "preparation_state": entry.preparation_state,
        "quantity_grams": entry.quantity_grams,
        "calories": entry.calories,
        "protein_g": entry.protein_g,
        "carbs_g": entry.carbs_g,
        "fat_g": entry.fat_g,
        "cost_inr": entry.cost_inr,
    }


@router.get("/logs")
async def get_daily_food_logs(
    log_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns food logs for the specified date and deterministic daily calorie/macro aggregation."""
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        return {"logs": [], "totals": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "cost_inr": 0}}

    target_date = date.fromisoformat(log_date) if log_date else date.today()
    res = await db.execute(
        select(FoodLog)
        .where(FoodLog.athlete_profile_id == profile.id, FoodLog.log_date == target_date)
        .order_by(FoodLog.created_at.asc())
    )
    logs = res.scalars().all()

    totals = {
        "calories": round(sum(l.calories for l in logs), 1),
        "protein_g": round(sum(l.protein_g for l in logs), 1),
        "carbs_g": round(sum(l.carbs_g for l in logs), 1),
        "fat_g": round(sum(l.fat_g for l in logs), 1),
        "cost_inr": round(sum(l.cost_inr for l in logs), 2),
    }

    return {
        "log_date": target_date.isoformat(),
        "totals": totals,
        "logs": [
            {
                "id": str(l.id),
                "meal_type": l.meal_type,
                "food_name": l.food_name,
                "preparation_state": l.preparation_state,
                "quantity_grams": l.quantity_grams,
                "calories": l.calories,
                "protein_g": l.protein_g,
                "carbs_g": l.carbs_g,
                "fat_g": l.fat_g,
                "cost_inr": l.cost_inr,
            }
            for l in logs
        ],
    }
