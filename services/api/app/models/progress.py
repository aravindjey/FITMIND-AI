import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Date, DateTime, Boolean, JSON, Text

from app.core.database import Base
from app.models.base import GUID, TimestampMixin


class BodyMeasurement(Base, TimestampMixin):
    __tablename__ = "body_measurements"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    athlete_profile_id = Column(GUID(), ForeignKey("athlete_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_at = Column(Date, nullable=False, index=True)
    weight_kg = Column(Float, nullable=True)
    waist_cm = Column(Float, nullable=True)
    chest_cm = Column(Float, nullable=True)
    hips_cm = Column(Float, nullable=True)
    shoulders_cm = Column(Float, nullable=True)
    bicep_left_cm = Column(Float, nullable=True)
    bicep_right_cm = Column(Float, nullable=True)
    thigh_left_cm = Column(Float, nullable=True)
    thigh_right_cm = Column(Float, nullable=True)
    calf_cm = Column(Float, nullable=True)
    neck_cm = Column(Float, nullable=True)
    notes = Column(String(500), nullable=True)


class ProgressPhoto(Base, TimestampMixin):
    __tablename__ = "progress_photos"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    athlete_profile_id = Column(GUID(), ForeignKey("athlete_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    taken_at = Column(Date, nullable=False, index=True)
    photo_type = Column(String(30), default="front", nullable=False)  # front | side | back
    storage_key = Column(String(500), nullable=False)
    mime_type = Column(String(50), default="image/jpeg", nullable=False)
    file_size_bytes = Column(Float, default=0.0, nullable=False)
    weight_at_capture_kg = Column(Float, nullable=True)
    analysis_results = Column(JSON, nullable=True)
    model_version = Column(String(100), nullable=True)
    is_fallback = Column(Boolean, default=False, nullable=False)


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="workout", nullable=False)  # workout | meal | hydration | check_in | recovery | sleep | system
    scheduled_time = Column(String(20), nullable=False)  # e.g. "07:00" or ISO timestamp
    days_of_week = Column(JSON, default=list, nullable=False)  # ["Mon", "Tue", ...]
    is_enabled = Column(Boolean, default=True, nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
