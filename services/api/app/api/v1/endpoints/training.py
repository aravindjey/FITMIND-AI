from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.workout import (
    Exercise,
    WorkoutPlan,
    WorkoutDay,
    WorkoutExercise,
    WorkoutSession,
    SetLog,
    PersonalRecord,
)
from app.repositories.athlete_repository import AthleteRepository
from app.repositories.audit_repository import AuditRepository
from app.services.seed_data import ensure_seed_data
from app.services.state_hydrator import AthleteStateHydrator
from app.agents.base import AgentInputEnvelope, AgentRunner
from app.agents.training_agent import TrainingAgent
from app.engines.one_rep_max import estimate_1rm
from app.engines.workout_engine import calculate_session_volume, calculate_next_load_prescription

router = APIRouter()


class SetLogInput(BaseModel):
    exercise_id: Optional[uuid.UUID] = None
    exercise_name: str
    set_number: int = Field(..., ge=1)
    weight_kg: float = Field(..., ge=0.0)
    reps_completed: int = Field(..., ge=0)
    actual_rpe: Optional[float] = Field(8.0, ge=1.0, le=10.0)
    is_warmup: bool = False


class WorkoutSessionCreate(BaseModel):
    workout_day_id: Optional[uuid.UUID] = None
    workout_name: str = "Training Session"
    session_rpe: Optional[float] = Field(8.0, ge=1.0, le=10.0)
    user_notes: Optional[str] = None
    sets: List[SetLogInput] = Field(default_factory=list)


class SubstituteExerciseRequest(BaseModel):
    exercise_name: str
    available_equipment: List[str] = Field(default_factory=lambda: ["bodyweight", "dumbbell", "barbell"])


@router.get("/exercises")
async def list_exercises(
    muscle_group: Optional[str] = None,
    equipment: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the curated exercise library, seeding defaults if empty."""
    await ensure_seed_data(db)
    query = select(Exercise).order_by(Exercise.primary_muscle_group, Exercise.name)
    if muscle_group:
        query = query.where(Exercise.primary_muscle_group == muscle_group.lower().strip())
    if equipment:
        query = query.where(Exercise.equipment_required == equipment.lower().strip())

    res = await db.execute(query)
    exercises = res.scalars().all()
    return [
        {
            "id": str(ex.id),
            "name": ex.name,
            "category": ex.category,
            "primary_muscle_group": ex.primary_muscle_group,
            "secondary_muscles": ex.secondary_muscles,
            "equipment_required": ex.equipment_required,
            "movement_pattern": ex.movement_pattern,
            "difficulty_level": ex.difficulty_level,
            "instructions": ex.instructions,
        }
        for ex in exercises
    ]


@router.post("/generate-plan", status_code=status.HTTP_201_CREATED)
async def generate_workout_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates, validates, and persists a personalized workout plan for the current athlete."""
    await ensure_seed_data(db)
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete your athlete profile or onboarding before generating a workout plan."
        )

    hydrator = AthleteStateHydrator(db)
    state = await hydrator.get_hydrated_state(current_user.id)

    agent = TrainingAgent()
    runner = AgentRunner(audit_repo=AuditRepository(db))
    envelope = AgentInputEnvelope(
        user_id=current_user.id,
        action="generate_workout",
        context_data=state,
        user_prompt="Generate personalized periodized workout plan",
    )
    output = await runner.run_agent(agent, envelope)
    if not output.validation_passed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Workout plan failed safety validation: {output.result_data.get('safety_validation')}"
        )

    # Deactivate old plans
    old_res = await db.execute(
        select(WorkoutPlan).where(WorkoutPlan.athlete_profile_id == profile.id, WorkoutPlan.is_active == True)
    )
    for old_plan in old_res.scalars().all():
        old_plan.is_active = False

    # Map exercise names to Exercise IDs
    ex_res = await db.execute(select(Exercise))
    ex_by_name = {ex.name.lower(): ex for ex in ex_res.scalars().all()}
    fallback_ex = next(iter(ex_by_name.values()))

    plan_data = output.result_data
    new_plan = WorkoutPlan(
        athlete_profile_id=profile.id,
        name=plan_data["plan_name"],
        description=output.explanation,
        training_split=plan_data["training_split"],
        duration_weeks=plan_data.get("duration_weeks", 4),
        days_per_week=plan_data.get("days_per_week", 4),
        is_active=True,
        generated_by_agent=agent.agent_name,
        is_fallback=output.is_fallback,
    )
    db.add(new_plan)
    await db.flush()

    for d_data in plan_data.get("days", []):
        w_day = WorkoutDay(
            workout_plan_id=new_plan.id,
            day_number=d_data["day_number"],
            name=d_data["name"],
            target_focus=d_data["target_focus"],
            scheduled_weekday=d_data.get("scheduled_weekday"),
        )
        db.add(w_day)
        await db.flush()

        for ex_item in d_data.get("exercises", []):
            ex_name = ex_item["exercise_name"]
            matched_ex = ex_by_name.get(ex_name.lower(), fallback_ex)
            w_ex = WorkoutExercise(
                workout_day_id=w_day.id,
                exercise_id=matched_ex.id,
                exercise_name=ex_name,
                order_in_workout=ex_item.get("order_in_workout", 1),
                target_sets=ex_item.get("target_sets", 3),
                target_rep_range_min=ex_item.get("target_rep_range_min", 8),
                target_rep_range_max=ex_item.get("target_rep_range_max", 12),
                prescribed_weight_kg=ex_item.get("prescribed_weight_kg", 0.0),
                target_rpe=ex_item.get("target_rpe", 8.0),
                rest_seconds=ex_item.get("rest_seconds", 90),
                tempo=ex_item.get("tempo", "2-0-1-0"),
                progression_rule=ex_item.get("progression_rule"),
                notes=ex_item.get("notes"),
            )
            db.add(w_ex)

    await db.commit()
    return await get_active_workout_plan(current_user=current_user, db=db)


@router.get("/active-plan")
async def get_active_workout_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetches the athlete's currently active workout plan."""
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        return {"has_active_plan": False, "plan": None}

    res = await db.execute(
        select(WorkoutPlan)
        .options(selectinload(WorkoutPlan.workout_days).selectinload(WorkoutDay.workout_exercises))
        .where(WorkoutPlan.athlete_profile_id == profile.id, WorkoutPlan.is_active == True)
        .order_by(WorkoutPlan.created_at.desc())
    )
    plan = res.scalars().first()
    if not plan:
        return {"has_active_plan": False, "plan": None}

    return {
        "has_active_plan": True,
        "plan": {
            "id": str(plan.id),
            "name": plan.name,
            "description": plan.description,
            "training_split": plan.training_split,
            "duration_weeks": plan.duration_weeks,
            "days_per_week": plan.days_per_week,
            "is_fallback": plan.is_fallback,
            "created_at": plan.created_at.isoformat(),
            "days": [
                {
                    "id": str(d.id),
                    "day_number": d.day_number,
                    "name": d.name,
                    "target_focus": d.target_focus,
                    "scheduled_weekday": d.scheduled_weekday,
                    "exercises": [
                        {
                            "id": str(ex.id),
                            "exercise_id": str(ex.exercise_id),
                            "exercise_name": ex.exercise_name,
                            "order_in_workout": ex.order_in_workout,
                            "target_sets": ex.target_sets,
                            "target_rep_range_min": ex.target_rep_range_min,
                            "target_rep_range_max": ex.target_rep_range_max,
                            "prescribed_weight_kg": ex.prescribed_weight_kg,
                            "target_rpe": ex.target_rpe,
                            "rest_seconds": ex.rest_seconds,
                            "tempo": ex.tempo,
                            "progression_rule": ex.progression_rule,
                            "notes": ex.notes,
                        }
                        for ex in d.workout_exercises
                    ],
                }
                for d in plan.workout_days
            ],
        },
    }


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def log_workout_session(
    session_in: WorkoutSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logs a completed workout session, calculates 1RM & tonnage, detects PRs,
    and returns deterministic next-session load prescriptions.
    """
    await ensure_seed_data(db)
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Athlete profile required before logging workout sessions."
        )

    ex_res = await db.execute(select(Exercise))
    ex_by_name = {ex.name.lower(): ex for ex in ex_res.scalars().all()}
    default_ex = next(iter(ex_by_name.values()))

    # Fetch existing PRs for comparison
    pr_res = await db.execute(
        select(PersonalRecord).where(PersonalRecord.athlete_profile_id == profile.id)
    )
    existing_prs: Dict[str, float] = {}
    for pr in pr_res.scalars().all():
        key = pr.exercise_name.lower()
        if pr.estimated_1rm_kg > existing_prs.get(key, 0.0):
            existing_prs[key] = pr.estimated_1rm_kg

    vol_stats = calculate_session_volume([s.model_dump() for s in session_in.sets])
    now_dt = datetime.now(timezone.utc)

    ws = WorkoutSession(
        athlete_profile_id=profile.id,
        workout_day_id=session_in.workout_day_id,
        workout_name=session_in.workout_name,
        started_at=now_dt,
        completed_at=now_dt,
        session_rpe=session_in.session_rpe,
        total_volume_kg=vol_stats["total_volume_kg"],
        user_notes=session_in.user_notes,
    )
    db.add(ws)
    await db.flush()

    new_prs_achieved: List[Dict[str, Any]] = []
    next_prescriptions: List[Dict[str, Any]] = []

    for s_in in session_in.sets:
        matched_ex = ex_by_name.get(s_in.exercise_name.lower(), default_ex)
        est_1rm = estimate_1rm(s_in.weight_kg, s_in.reps_completed) if not s_in.is_warmup else 0.0
        ex_key = s_in.exercise_name.lower()

        is_pr = False
        if not s_in.is_warmup and est_1rm > existing_prs.get(ex_key, 0.0) and est_1rm > 0:
            is_pr = True
            existing_prs[ex_key] = est_1rm
            pr_record = PersonalRecord(
                athlete_profile_id=profile.id,
                exercise_id=matched_ex.id,
                exercise_name=s_in.exercise_name,
                weight_kg=s_in.weight_kg,
                reps=s_in.reps_completed,
                estimated_1rm_kg=est_1rm,
                achieved_at=date.today(),
            )
            db.add(pr_record)
            new_prs_achieved.append({
                "exercise_name": s_in.exercise_name,
                "weight_kg": s_in.weight_kg,
                "reps": s_in.reps_completed,
                "estimated_1rm_kg": est_1rm,
            })

        set_log = SetLog(
            workout_session_id=ws.id,
            exercise_id=matched_ex.id,
            exercise_name=s_in.exercise_name,
            set_number=s_in.set_number,
            weight_kg=s_in.weight_kg,
            reps_completed=s_in.reps_completed,
            actual_rpe=s_in.actual_rpe,
            estimated_1rm_kg=est_1rm,
            is_warmup=s_in.is_warmup,
            is_pr=is_pr,
        )
        db.add(set_log)

        if not s_in.is_warmup:
            next_presc = calculate_next_load_prescription(
                current_weight_kg=s_in.weight_kg,
                reps_completed=s_in.reps_completed,
                target_rep_min=8,
                target_rep_max=12,
                actual_rpe=s_in.actual_rpe,
                target_rpe=8.0,
            )
            next_prescriptions.append({
                "exercise_name": s_in.exercise_name,
                "set_number": s_in.set_number,
                **next_presc,
            })

    await db.commit()
    return {
        "session_id": str(ws.id),
        "workout_name": ws.workout_name,
        "total_volume_kg": ws.total_volume_kg,
        "working_sets": vol_stats["working_sets"],
        "new_personal_records": new_prs_achieved,
        "next_session_prescriptions": next_prescriptions,
    }


@router.get("/sessions")
async def list_workout_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists workout session history for the current athlete."""
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        return []

    res = await db.execute(
        select(WorkoutSession)
        .options(selectinload(WorkoutSession.set_logs))
        .where(WorkoutSession.athlete_profile_id == profile.id)
        .order_by(WorkoutSession.started_at.desc())
        .limit(30)
    )
    sessions = res.scalars().all()
    return [
        {
            "id": str(s.id),
            "workout_name": s.workout_name,
            "started_at": s.started_at.isoformat(),
            "session_rpe": s.session_rpe,
            "total_volume_kg": s.total_volume_kg,
            "user_notes": s.user_notes,
            "sets": [
                {
                    "id": str(sl.id),
                    "exercise_name": sl.exercise_name,
                    "set_number": sl.set_number,
                    "weight_kg": sl.weight_kg,
                    "reps_completed": sl.reps_completed,
                    "actual_rpe": sl.actual_rpe,
                    "estimated_1rm_kg": sl.estimated_1rm_kg,
                    "is_pr": sl.is_pr,
                }
                for sl in s.set_logs
            ],
        }
        for s in sessions
    ]


@router.get("/prs")
async def list_personal_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns personal records achieved by the current athlete."""
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        return []

    res = await db.execute(
        select(PersonalRecord)
        .where(PersonalRecord.athlete_profile_id == profile.id)
        .order_by(PersonalRecord.achieved_at.desc(), PersonalRecord.estimated_1rm_kg.desc())
    )
    return [
        {
            "id": str(pr.id),
            "exercise_name": pr.exercise_name,
            "weight_kg": pr.weight_kg,
            "reps": pr.reps,
            "estimated_1rm_kg": pr.estimated_1rm_kg,
            "achieved_at": pr.achieved_at.isoformat(),
        }
        for pr in res.scalars().all()
    ]


@router.post("/substitute")
async def substitute_exercise(
    sub_in: SubstituteExerciseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Finds biomechanically equivalent exercise substitutions matching movement pattern and muscle group."""
    await ensure_seed_data(db)
    res = await db.execute(select(Exercise))
    all_ex = res.scalars().all()

    target = next((e for e in all_ex if e.name.lower() == sub_in.exercise_name.lower().strip()), None)
    allowed_eq = {e.lower().strip() for e in sub_in.available_equipment}
    allowed_eq.add("bodyweight")

    if not target:
        candidates = [e for e in all_ex if e.equipment_required.lower() in allowed_eq][:4]
    else:
        candidates = [
            e for e in all_ex
            if e.id != target.id
            and (e.movement_pattern == target.movement_pattern or e.primary_muscle_group == target.primary_muscle_group)
            and e.equipment_required.lower() in allowed_eq
        ]

    return {
        "original_exercise": sub_in.exercise_name,
        "substitutions": [
            {
                "id": str(c.id),
                "name": c.name,
                "primary_muscle_group": c.primary_muscle_group,
                "movement_pattern": c.movement_pattern,
                "equipment_required": c.equipment_required,
                "instructions": c.instructions,
            }
            for c in candidates[:5]
        ],
    }
