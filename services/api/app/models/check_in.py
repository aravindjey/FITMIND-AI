import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean, Date, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import GUID, TimestampMixin


class CheckIn(Base, TimestampMixin):
    __tablename__ = "check_ins"
    __table_args__ = (
        UniqueConstraint("athlete_profile_id", "check_in_date", name="uq_athlete_check_in_date"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    athlete_profile_id = Column(GUID(), ForeignKey("athlete_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    check_in_date = Column(Date, nullable=False)
    weight_kg = Column(Float, nullable=False)
    energy_score = Column(Integer, nullable=True)
    sleep_hours = Column(Float, nullable=True)
    sleep_quality_score = Column(Integer, nullable=True)
    stress_score = Column(Integer, nullable=True)
    soreness_score = Column(Integer, nullable=True)
    hydration_liters = Column(Float, nullable=True)
    nutrition_adherence_percent = Column(Integer, nullable=True)
    workout_completed = Column(Boolean, default=False, nullable=False)
    notes = Column(String(1000), nullable=True)

    # Relationships
    athlete_profile = relationship("AthleteProfile", back_populates="check_ins")
