import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import GUID, TimestampMixin


class NutritionProfile(Base, TimestampMixin):
    __tablename__ = "nutrition_profiles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    athlete_profile_id = Column(GUID(), ForeignKey("athlete_profiles.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    bmr_kcal = Column(Integer, nullable=False)
    tdee_kcal = Column(Integer, nullable=False)
    target_calories = Column(Integer, nullable=False)
    protein_grams = Column(Integer, nullable=False)
    carbs_grams = Column(Integer, nullable=False)
    fat_grams = Column(Integer, nullable=False)
    weekly_food_budget_amount = Column(Float, nullable=True)
    currency_code = Column(String(3), default="INR", nullable=False)
    meals_per_day = Column(Integer, default=4, nullable=False)

    # Relationships
    athlete_profile = relationship("AthleteProfile", back_populates="nutrition_profile")
