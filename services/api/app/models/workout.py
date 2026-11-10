import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean, DateTime, Text, JSON, Date
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import GUID, TimestampMixin


class Exercise(Base, TimestampMixin):
    __tablename__ = "exercises"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)  # barbell | dumbbell | machine | bodyweight | cables | cardio | other
    primary_muscle_group = Column(String(50), nullable=False, index=True)
    secondary_muscles = Column(JSON, default=list, nullable=False)
    equipment_required = Column(String(50), nullable=False)
    movement_pattern = Column(String(50), nullable=False)  # squat | hinge | horizontal_push | horizontal_pull | vertical_push | vertical_pull | carry | isolation
    difficulty_level = Column(String(30), default="intermediate", nullable=False)
    instructions = Column(Text, nullable=True)


class WorkoutPlan(Base, TimestampMixin):
    __tablename__ = "workout_plans"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    athlete_profile_id = Column(GUID(), ForeignKey("athlete_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    training_split = Column(String(50), default="upper_lower", nullable=False)  # full_body | upper_lower | push_pull_legs | powerlifting | bodybuilding
    duration_weeks = Column(Integer, default=4, nullable=False)
    days_per_week = Column(Integer, default=4, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    generated_by_agent = Column(String(50), default="TrainingAgent", nullable=False)
    is_fallback = Column(Boolean, default=False, nullable=False)

    # Relationships
    workout_days = relationship("WorkoutDay", back_populates="workout_plan", cascade="all, delete-orphan", lazy="selectin", order_by="WorkoutDay.day_number")


class WorkoutDay(Base, TimestampMixin):
    __tablename__ = "workout_days"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    workout_plan_id = Column(GUID(), ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    day_number = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    target_focus = Column(String(100), nullable=False)
    scheduled_weekday = Column(String(20), nullable=True)

    # Relationships
    workout_plan = relationship("WorkoutPlan", back_populates="workout_days")
    workout_exercises = relationship("WorkoutExercise", back_populates="workout_day", cascade="all, delete-orphan", lazy="selectin", order_by="WorkoutExercise.order_in_workout")


class WorkoutExercise(Base, TimestampMixin):
    __tablename__ = "workout_exercises"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    workout_day_id = Column(GUID(), ForeignKey("workout_days.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(GUID(), ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    exercise_name = Column(String(150), nullable=False)
    order_in_workout = Column(Integer, nullable=False)
    target_sets = Column(Integer, nullable=False)
    target_rep_range_min = Column(Integer, nullable=False)
    target_rep_range_max = Column(Integer, nullable=False)
    prescribed_weight_kg = Column(Float, nullable=True)
    target_rpe = Column(Float, default=8.0, nullable=True)
    rest_seconds = Column(Integer, default=90, nullable=False)
    tempo = Column(String(20), default="2-0-1-0", nullable=True)
    progression_rule = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    workout_day = relationship("WorkoutDay", back_populates="workout_exercises")
    exercise = relationship("Exercise", lazy="selectin")


class WorkoutSession(Base, TimestampMixin):
    __tablename__ = "workout_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    athlete_profile_id = Column(GUID(), ForeignKey("athlete_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    workout_day_id = Column(GUID(), ForeignKey("workout_days.id", ondelete="SET NULL"), nullable=True)
    workout_name = Column(String(150), default="Training Session", nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    session_rpe = Column(Float, nullable=True)
    total_volume_kg = Column(Float, default=0.0, nullable=False)
    user_notes = Column(Text, nullable=True)

    # Relationships
    set_logs = relationship("SetLog", back_populates="workout_session", cascade="all, delete-orphan", lazy="selectin", order_by="SetLog.set_number")


class SetLog(Base, TimestampMixin):
    __tablename__ = "set_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    workout_session_id = Column(GUID(), ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    workout_exercise_id = Column(GUID(), ForeignKey("workout_exercises.id", ondelete="SET NULL"), nullable=True)
    exercise_id = Column(GUID(), ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    exercise_name = Column(String(150), nullable=False)
    set_number = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=False)
    reps_completed = Column(Integer, nullable=False)
    actual_rpe = Column(Float, nullable=True)
    estimated_1rm_kg = Column(Float, default=0.0, nullable=False)
    is_warmup = Column(Boolean, default=False, nullable=False)
    is_pr = Column(Boolean, default=False, nullable=False)

    # Relationships
    workout_session = relationship("WorkoutSession", back_populates="set_logs")


class PersonalRecord(Base, TimestampMixin):
    __tablename__ = "personal_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    athlete_profile_id = Column(GUID(), ForeignKey("athlete_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(GUID(), ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    exercise_name = Column(String(150), nullable=False)
    weight_kg = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)
    estimated_1rm_kg = Column(Float, nullable=False)
    achieved_at = Column(Date, nullable=False)
