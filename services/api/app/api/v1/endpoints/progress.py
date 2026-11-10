from typing import Optional, List, Dict, Any
from datetime import date
import uuid
import base64
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.check_in import CheckIn
from app.models.progress import BodyMeasurement, ProgressPhoto, Notification
from app.models.workout import WorkoutSession, PersonalRecord
from app.repositories.athlete_repository import AthleteRepository
from app.repositories.audit_repository import AuditRepository
from app.engines.weight_trend import calculate_ema_weight_trend, calculate_rate_of_change
from app.engines.workout_engine import calculate_recovery_readiness
from app.agents.base import AgentInputEnvelope, AgentRunner
from app.agents.stubs import BodyAnalysisAgent, RecoveryAgent, LifestyleHabitAgent, ProgressAgent

router = APIRouter()


class DailyCheckInRequest(BaseModel):
    check_in_date: Optional[str] = None  # YYYY-MM-DD
    weight_kg: float = Field(..., gt=20, lt=500)
    energy_score: int = Field(7, ge=1, le=10)
    sleep_hours: float = Field(7.5, ge=0.0, le=24.0)
    sleep_quality_score: int = Field(7, ge=1, le=10)
    stress_score: int = Field(4, ge=1, le=10)
    soreness_score: int = Field(3, ge=1, le=10)
    hydration_liters: float = Field(3.0, ge=0.0, le=15.0)
    nutrition_adherence_percent: int = Field(90, ge=0, le=100)
    workout_completed: bool = True
    notes: Optional[str] = None


class BodyMeasurementCreateRequest(BaseModel):
    recorded_at: Optional[str] = None
    weight_kg: Optional[float] = Field(None, gt=20, lt=500)
    waist_cm: Optional[float] = Field(None, gt=30, lt=250)
    chest_cm: Optional[float] = Field(None, gt=40, lt=250)
    hips_cm: Optional[float] = Field(None, gt=40, lt=250)
    shoulders_cm: Optional[float] = Field(None, gt=40, lt=250)
    bicep_left_cm: Optional[float] = Field(None, gt=15, lt=100)
    bicep_right_cm: Optional[float] = Field(None, gt=15, lt=100)
    thigh_left_cm: Optional[float] = Field(None, gt=25, lt=150)
    thigh_right_cm: Optional[float] = Field(None, gt=25, lt=150)
    notes: Optional[str] = None


class ProgressPhotoAnalyzeRequest(BaseModel):
    photo_type: str = Field(default="front", description="front, side, or back")
    taken_at: Optional[str] = None
    weight_at_capture_kg: Optional[float] = None
    image_base64: Optional[str] = None
    filename: str = "progress_photo.jpg"


class ReminderCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    message: str = Field(default="Scheduled coaching reminder")
    notification_type: str = Field(default="workout")  # workout | meal | hydration | check_in | recovery | sleep
    scheduled_time: str = Field(default="07:30")
    days_of_week: List[str] = Field(default_factory=lambda: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    is_enabled: bool = True


@router.post("/check-ins", status_code=status.HTTP_201_CREATED)
async def submit_daily_check_in(
    checkin_in: DailyCheckInRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logs a daily check-in, updates current weight & historical measurements,
    and executes RecoveryAgent + LifestyleHabitAgent.
    """
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Athlete profile required before logging daily check-ins."
        )

    target_date = date.fromisoformat(checkin_in.check_in_date) if checkin_in.check_in_date else date.today()

    existing_res = await db.execute(
        select(CheckIn).where(
            CheckIn.athlete_profile_id == profile.id,
            CheckIn.check_in_date == target_date,
        )
    )
    checkin = existing_res.scalars().first()
    if not checkin:
        checkin = CheckIn(athlete_profile_id=profile.id, check_in_date=target_date)
        db.add(checkin)

    checkin.weight_kg = checkin_in.weight_kg
    checkin.energy_score = checkin_in.energy_score
    checkin.sleep_hours = checkin_in.sleep_hours
    checkin.sleep_quality_score = checkin_in.sleep_quality_score
    checkin.stress_score = checkin_in.stress_score
    checkin.soreness_score = checkin_in.soreness_score
    checkin.hydration_liters = checkin_in.hydration_liters
    checkin.nutrition_adherence_percent = checkin_in.nutrition_adherence_percent
    checkin.workout_completed = checkin_in.workout_completed
    checkin.notes = checkin_in.notes

    # Update profile's current weight and append historical weight record
    profile.current_weight_kg = checkin_in.weight_kg
    db.add(BodyMeasurement(
        athlete_profile_id=profile.id,
        recorded_at=target_date,
        weight_kg=checkin_in.weight_kg,
        notes="Daily check-in weight log",
    ))

    await db.commit()
    await db.refresh(checkin)

    # Count check-in streak
    all_ci_res = await db.execute(
        select(CheckIn).where(CheckIn.athlete_profile_id == profile.id).order_by(CheckIn.check_in_date.desc())
    )
    streak_count = len(all_ci_res.scalars().all())

    runner = AgentRunner(audit_repo=AuditRepository(db))
    rec_agent = RecoveryAgent()
    hab_agent = LifestyleHabitAgent()

    rec_out = await runner.run_agent(
        rec_agent,
        AgentInputEnvelope(
            user_id=current_user.id,
            action="evaluate_recovery",
            context_data={"check_in_metrics": checkin_in.model_dump()},
        ),
    )
    hab_out = await runner.run_agent(
        hab_agent,
        AgentInputEnvelope(
            user_id=current_user.id,
            action="evaluate_habits",
            context_data={
                "latest_check_in": checkin_in.model_dump(),
                "checkin_streak_days": streak_count,
            },
        ),
    )

    return {
        "check_in": {
            "id": str(checkin.id),
            "check_in_date": checkin.check_in_date.isoformat(),
            "weight_kg": checkin.weight_kg,
            "energy_score": checkin.energy_score,
            "sleep_hours": checkin.sleep_hours,
            "sleep_quality_score": checkin.sleep_quality_score,
            "stress_score": checkin.stress_score,
            "soreness_score": checkin.soreness_score,
            "hydration_liters": checkin.hydration_liters,
            "nutrition_adherence_percent": checkin.nutrition_adherence_percent,
            "workout_completed": checkin.workout_completed,
            "notes": checkin.notes,
        },
        "recovery_assessment": rec_out.result_data,
        "lifestyle_insights": hab_out.result_data,
    }


@router.get("/check-ins")
async def list_check_ins(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns daily check-ins, 7-day EMA weight trend, and latest recovery readiness."""
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        return {"check_ins": [], "weight_trend": {}, "latest_recovery": None}

    res = await db.execute(
        select(CheckIn)
        .where(CheckIn.athlete_profile_id == profile.id)
        .order_by(CheckIn.check_in_date.asc())
    )
    items = res.scalars().all()
    weights = [c.weight_kg for c in items] if items else [profile.current_weight_kg]
    ema_series = calculate_ema_weight_trend(weights)
    weekly_rate = calculate_rate_of_change(weights)

    latest = items[-1] if items else None
    latest_recovery = (
        calculate_recovery_readiness(
            sleep_hours=latest.sleep_hours or 7.5,
            sleep_quality_score=latest.sleep_quality_score or 7,
            energy_score=latest.energy_score or 7,
            soreness_score=latest.soreness_score or 3,
            stress_score=latest.stress_score or 4,
        )
        if latest
        else None
    )

    return {
        "check_ins": [
            {
                "id": str(c.id),
                "check_in_date": c.check_in_date.isoformat(),
                "weight_kg": c.weight_kg,
                "ema_weight_kg": ema_series[idx],
                "energy_score": c.energy_score,
                "sleep_hours": c.sleep_hours,
                "sleep_quality_score": c.sleep_quality_score,
                "stress_score": c.stress_score,
                "soreness_score": c.soreness_score,
                "hydration_liters": c.hydration_liters,
                "nutrition_adherence_percent": c.nutrition_adherence_percent,
                "workout_completed": c.workout_completed,
                "notes": c.notes,
            }
            for idx, c in enumerate(items)
        ],
        "weight_trend": {
            "current_weight_kg": profile.current_weight_kg,
            "ema_latest_kg": ema_series[-1] if ema_series else profile.current_weight_kg,
            "weekly_rate_kg": weekly_rate,
            "ema_series": ema_series,
        },
        "latest_recovery": latest_recovery,
    }


@router.post("/measurements", status_code=status.HTTP_201_CREATED)
async def create_body_measurement(
    meas_in: BodyMeasurementCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(status_code=400, detail="Athlete profile required.")

    rec_date = date.fromisoformat(meas_in.recorded_at) if meas_in.recorded_at else date.today()
    bm = BodyMeasurement(
        athlete_profile_id=profile.id,
        recorded_at=rec_date,
        weight_kg=meas_in.weight_kg or profile.current_weight_kg,
        waist_cm=meas_in.waist_cm,
        chest_cm=meas_in.chest_cm,
        hips_cm=meas_in.hips_cm,
        shoulders_cm=meas_in.shoulders_cm,
        bicep_left_cm=meas_in.bicep_left_cm,
        bicep_right_cm=meas_in.bicep_right_cm,
        thigh_left_cm=meas_in.thigh_left_cm,
        thigh_right_cm=meas_in.thigh_right_cm,
        notes=meas_in.notes,
    )
    if meas_in.weight_kg:
        profile.current_weight_kg = meas_in.weight_kg

    db.add(bm)
    await db.commit()
    await db.refresh(bm)
    return {
        "id": str(bm.id),
        "recorded_at": bm.recorded_at.isoformat(),
        "weight_kg": bm.weight_kg,
        "waist_cm": bm.waist_cm,
        "chest_cm": bm.chest_cm,
        "hips_cm": bm.hips_cm,
        "shoulders_cm": bm.shoulders_cm,
        "bicep_left_cm": bm.bicep_left_cm,
        "bicep_right_cm": bm.bicep_right_cm,
        "thigh_left_cm": bm.thigh_left_cm,
        "thigh_right_cm": bm.thigh_right_cm,
        "notes": bm.notes,
    }


@router.get("/measurements")
async def list_body_measurements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        return []

    res = await db.execute(
        select(BodyMeasurement)
        .where(BodyMeasurement.athlete_profile_id == profile.id)
        .order_by(BodyMeasurement.recorded_at.desc(), BodyMeasurement.created_at.desc())
        .limit(50)
    )
    return [
        {
            "id": str(bm.id),
            "recorded_at": bm.recorded_at.isoformat(),
            "weight_kg": bm.weight_kg,
            "waist_cm": bm.waist_cm,
            "chest_cm": bm.chest_cm,
            "hips_cm": bm.hips_cm,
            "shoulders_cm": bm.shoulders_cm,
            "bicep_left_cm": bm.bicep_left_cm,
            "bicep_right_cm": bm.bicep_right_cm,
            "thigh_left_cm": bm.thigh_left_cm,
            "thigh_right_cm": bm.thigh_right_cm,
            "notes": bm.notes,
        }
        for bm in res.scalars().all()
    ]


@router.get("/analytics")
async def get_progress_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregates real database records for weight trends, training volume, PRs, and consistency."""
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        return {"has_profile": False}

    bm_res = await db.execute(
        select(BodyMeasurement)
        .where(BodyMeasurement.athlete_profile_id == profile.id, BodyMeasurement.weight_kg != None)
        .order_by(BodyMeasurement.recorded_at.asc(), BodyMeasurement.created_at.asc())
    )
    bm_list = bm_res.scalars().all()
    weights = [float(b.weight_kg) for b in bm_list if b.weight_kg is not None] or [profile.current_weight_kg]
    ema_weights = calculate_ema_weight_trend(weights)
    weekly_rate = calculate_rate_of_change(weights)

    ws_res = await db.execute(
        select(WorkoutSession)
        .where(WorkoutSession.athlete_profile_id == profile.id)
        .order_by(WorkoutSession.started_at.asc())
    )
    sessions = ws_res.scalars().all()

    pr_res = await db.execute(
        select(PersonalRecord)
        .where(PersonalRecord.athlete_profile_id == profile.id)
        .order_by(PersonalRecord.achieved_at.desc())
    )
    prs = pr_res.scalars().all()

    return {
        "has_profile": True,
        "current_weight_kg": profile.current_weight_kg,
        "ema_weight_kg": ema_weights[-1] if ema_weights else profile.current_weight_kg,
        "weekly_weight_rate_kg": weekly_rate,
        "weight_series": [
            {
                "date": b.recorded_at.isoformat(),
                "weight_kg": b.weight_kg,
                "ema_kg": ema_weights[idx],
            }
            for idx, b in enumerate(bm_list)
        ],
        "workout_volume_series": [
            {
                "date": s.started_at.date().isoformat(),
                "workout_name": s.workout_name,
                "total_volume_kg": s.total_volume_kg,
                "session_rpe": s.session_rpe,
            }
            for s in sessions
        ],
        "personal_records": [
            {
                "exercise_name": p.exercise_name,
                "weight_kg": p.weight_kg,
                "reps": p.reps,
                "estimated_1rm_kg": p.estimated_1rm_kg,
                "achieved_at": p.achieved_at.isoformat(),
            }
            for p in prs
        ],
        "total_workouts_logged": len(sessions),
        "total_tonnage_lifted_kg": round(sum(s.total_volume_kg for s in sessions), 1),
    }


@router.post("/photos/analyze", status_code=status.HTTP_201_CREATED)
async def upload_and_analyze_progress_photo(
    photo_in: ProgressPhotoAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validates and records a progress photograph, invokes BodyAnalysisAgent with explicit
    estimation uncertainty, and compares against previous photographs/measurements.
    """
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(status_code=400, detail="Athlete profile required.")

    if photo_in.photo_type not in ("front", "side", "back"):
        raise HTTPException(status_code=400, detail="photo_type must be 'front', 'side', or 'back'.")

    raw_bytes = b"progress_photo_placeholder"
    if photo_in.image_base64:
        try:
            clean_b64 = photo_in.image_base64.split(",")[-1]
            raw_bytes = base64.b64decode(clean_b64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image payload.")

    if len(raw_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds 10MB limit.")

    prev_res = await db.execute(
        select(ProgressPhoto)
        .where(ProgressPhoto.athlete_profile_id == profile.id)
        .order_by(ProgressPhoto.taken_at.desc(), ProgressPhoto.created_at.desc())
        .limit(1)
    )
    prev_photo = prev_res.scalars().first()

    capture_weight = photo_in.weight_at_capture_kg or profile.current_weight_kg
    runner = AgentRunner(audit_repo=AuditRepository(db))
    body_agent = BodyAnalysisAgent()
    out = await runner.run_agent(
        body_agent,
        AgentInputEnvelope(
            user_id=current_user.id,
            action="analyze_body_photo",
            context_data={
                "image_bytes": raw_bytes,
                "photo_type": photo_in.photo_type,
                "weight_kg": capture_weight,
                "previous_weight_kg": prev_photo.weight_at_capture_kg if prev_photo else None,
            },
        ),
    )

    cap_date = date.fromisoformat(photo_in.taken_at) if photo_in.taken_at else date.today()
    storage_key = f"vault/{current_user.id}/{cap_date.isoformat()}_{photo_in.photo_type}_{uuid.uuid4().hex[:8]}.jpg"

    photo_record = ProgressPhoto(
        athlete_profile_id=profile.id,
        taken_at=cap_date,
        photo_type=photo_in.photo_type,
        storage_key=storage_key,
        file_size_bytes=float(len(raw_bytes)),
        weight_at_capture_kg=capture_weight,
        analysis_results=out.result_data,
        model_version="fallback-vision-v1" if out.is_fallback else "vision-v1",
        is_fallback=out.is_fallback,
    )
    db.add(photo_record)
    await db.commit()
    await db.refresh(photo_record)

    return {
        "id": str(photo_record.id),
        "taken_at": photo_record.taken_at.isoformat(),
        "photo_type": photo_record.photo_type,
        "storage_key": photo_record.storage_key,
        "weight_at_capture_kg": photo_record.weight_at_capture_kg,
        "is_fallback": photo_record.is_fallback,
        "analysis": photo_record.analysis_results,
    }


@router.get("/photos")
async def list_progress_photos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = AthleteRepository(db)
    profile = await repo.get_by_user_id(current_user.id)
    if not profile:
        return []

    res = await db.execute(
        select(ProgressPhoto)
        .where(ProgressPhoto.athlete_profile_id == profile.id)
        .order_by(ProgressPhoto.taken_at.desc(), ProgressPhoto.created_at.desc())
    )
    return [
        {
            "id": str(p.id),
            "taken_at": p.taken_at.isoformat(),
            "photo_type": p.photo_type,
            "storage_key": p.storage_key,
            "weight_at_capture_kg": p.weight_at_capture_kg,
            "is_fallback": p.is_fallback,
            "analysis": p.analysis_results,
        }
        for p in res.scalars().all()
    ]


@router.post("/reminders", status_code=status.HTTP_201_CREATED)
async def create_reminder(
    rem_in: ReminderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notif = Notification(
        user_id=current_user.id,
        title=rem_in.title,
        message=rem_in.message,
        notification_type=rem_in.notification_type,
        scheduled_time=rem_in.scheduled_time,
        days_of_week=rem_in.days_of_week,
        is_enabled=rem_in.is_enabled,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return {
        "id": str(notif.id),
        "title": notif.title,
        "message": notif.message,
        "notification_type": notif.notification_type,
        "scheduled_time": notif.scheduled_time,
        "days_of_week": notif.days_of_week,
        "is_enabled": notif.is_enabled,
    }


@router.get("/reminders")
async def list_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.scheduled_time.asc())
    )
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "message": n.message,
            "notification_type": n.notification_type,
            "scheduled_time": n.scheduled_time,
            "days_of_week": n.days_of_week,
            "is_enabled": n.is_enabled,
        }
        for n in res.scalars().all()
    ]


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Notification).where(Notification.id == reminder_id, Notification.user_id == current_user.id)
    )
    notif = res.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    await db.delete(notif)
    await db.commit()
    return {"message": "Reminder deleted"}
