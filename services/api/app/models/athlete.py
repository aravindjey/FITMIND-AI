import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import GUID, TimestampMixin


class AthleteProfile(Base, TimestampMixin):
    __tablename__ = "athlete_profiles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    age = Column(Integer, nullable=False)
    sex = Column(String(20), nullable=False)  # male | female | other
    height_cm = Column(Float, nullable=False)
    current_weight_kg = Column(Float, nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    training_experience_years = Column(Float, default=0.0, nullable=False)
    activity_level = Column(String(30), nullable=False)  # sedentary | lightly_active | moderately_active | very_active | extra_active
    occupation_type = Column(String(100), nullable=True)
    
    sport_name = Column(String(100), nullable=True)
    sport_position = Column(String(50), nullable=True)
    training_preferences = Column(JSON, default=dict, nullable=False)

    # Relationships
    user = relationship("User", back_populates="athlete_profile")
    goals = relationship("Goal", back_populates="athlete_profile", cascade="all, delete-orphan", lazy="selectin")
    nutrition_profile = relationship("NutritionProfile", back_populates="athlete_profile", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    check_ins = relationship("CheckIn", back_populates="athlete_profile", cascade="all, delete-orphan", lazy="selectin")


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    athlete_profile_id = Column(GUID(), ForeignKey("athlete_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    primary_goal = Column(String(50), nullable=False)  # fat_loss | muscle_gain | strength | powerlifting | bodybuilding | sports_performance | general_fitness
    target_weight_kg = Column(Float, nullable=True)
    target_date = Column(String(20), nullable=True)  # YYYY-MM-DD
    sport_name = Column(String(100), nullable=True)
    sport_position = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    athlete_profile = relationship("AthleteProfile", back_populates="goals")
