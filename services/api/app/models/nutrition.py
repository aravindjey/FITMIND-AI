import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean, Text, JSON, Date
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
    dietary_type = Column(String(50), default="omnivore", nullable=False)  # vegetarian | eggetarian | vegan | omnivore | jain | halal

    # Relationships
    athlete_profile = relationship("AthleteProfile", back_populates="nutrition_profile")
    food_preferences = relationship("FoodPreference", back_populates="nutrition_profile", cascade="all, delete-orphan", lazy="selectin")
    nutrition_plans = relationship("NutritionPlan", back_populates="nutrition_profile", cascade="all, delete-orphan", lazy="selectin")


class FoodPreference(Base, TimestampMixin):
    __tablename__ = "food_preferences"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    nutrition_profile_id = Column(GUID(), ForeignKey("nutrition_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    food_name = Column(String(150), nullable=False)
    preference_type = Column(String(30), nullable=False)  # liked | disliked | allergic | avoided | staple

    # Relationships
    nutrition_profile = relationship("NutritionProfile", back_populates="food_preferences")


class FoodItem(Base, TimestampMixin):
    __tablename__ = "food_items"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)  # grain | pulse_dal | dairy_paneer | poultry_egg | meat_fish | vegetable | fruit | nut_seed | oil_fat | supplement
    preparation_state = Column(String(30), default="cooked", nullable=False)  # raw | cooked | ready_to_eat
    serving_unit = Column(String(50), default="100g", nullable=False)
    serving_grams = Column(Float, default=100.0, nullable=False)
    calories_per_100g = Column(Float, nullable=False)
    protein_per_100g = Column(Float, nullable=False)
    carbs_per_100g = Column(Float, nullable=False)
    fat_per_100g = Column(Float, nullable=False)
    fiber_per_100g = Column(Float, default=0.0, nullable=False)
    estimated_cost_inr_per_100g = Column(Float, default=15.0, nullable=False)
    is_vegetarian = Column(Boolean, default=True, nullable=False)
    is_vegan = Column(Boolean, default=False, nullable=False)
    is_indian_staple = Column(Boolean, default=True, nullable=False)


class NutritionPlan(Base, TimestampMixin):
    __tablename__ = "nutrition_plans"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    nutrition_profile_id = Column(GUID(), ForeignKey("nutrition_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    daily_calories = Column(Integer, nullable=False)
    protein_grams = Column(Integer, nullable=False)
    carbs_grams = Column(Integer, nullable=False)
    fat_grams = Column(Integer, nullable=False)
    estimated_daily_cost_inr = Column(Float, default=0.0, nullable=False)
    calculation_assumptions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    is_fallback = Column(Boolean, default=False, nullable=False)

    # Relationships
    nutrition_profile = relationship("NutritionProfile", back_populates="nutrition_plans")
    meals = relationship("Meal", back_populates="nutrition_plan", cascade="all, delete-orphan", lazy="selectin", order_by="Meal.meal_number")


class Meal(Base, TimestampMixin):
    __tablename__ = "meals"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    nutrition_plan_id = Column(GUID(), ForeignKey("nutrition_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    meal_number = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    time_of_day = Column(String(30), nullable=True)
    target_calories = Column(Integer, nullable=False)
    protein_g = Column(Integer, nullable=False)
    carbs_g = Column(Integer, nullable=False)
    fat_g = Column(Integer, nullable=False)
    estimated_cost_inr = Column(Float, default=0.0, nullable=False)
    recipe_instructions = Column(Text, nullable=True)
    ingredients = Column(JSON, default=list, nullable=False)

    # Relationships
    nutrition_plan = relationship("NutritionPlan", back_populates="meals")


class FoodLog(Base, TimestampMixin):
    __tablename__ = "food_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    athlete_profile_id = Column(GUID(), ForeignKey("athlete_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    food_item_id = Column(GUID(), ForeignKey("food_items.id", ondelete="SET NULL"), nullable=True)
    log_date = Column(Date, nullable=False, index=True)
    meal_type = Column(String(30), default="lunch", nullable=False)  # breakfast | lunch | snack | pre_workout | post_workout | dinner
    food_name = Column(String(150), nullable=False)
    preparation_state = Column(String(30), default="cooked", nullable=False)  # raw | cooked
    quantity_grams = Column(Float, nullable=False)
    calories = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    cost_inr = Column(Float, default=0.0, nullable=False)
