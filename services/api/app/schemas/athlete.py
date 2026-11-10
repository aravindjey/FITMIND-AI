from typing import Optional, Dict, Any, List
import uuid
from pydantic import BaseModel, Field, ConfigDict


class GoalSchema(BaseModel):
    id: Optional[uuid.UUID] = None
    primary_goal: str = Field(..., description="fat_loss, muscle_gain, strength, powerlifting, bodybuilding, sports_performance, general_fitness")
    target_weight_kg: Optional[float] = Field(None, gt=20, lt=500)
    target_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    sport_name: Optional[str] = None
    sport_position: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AthleteProfileCreate(BaseModel):
    age: int = Field(..., ge=13, le=100)
    sex: str = Field(..., description="male, female, or other")
    height_cm: float = Field(..., gt=50, lt=300)
    current_weight_kg: float = Field(..., gt=20, lt=500)
    timezone: str = Field(default="UTC")
    training_experience_years: float = Field(default=0.0, ge=0.0, le=70.0)
    activity_level: str = Field(..., description="sedentary, lightly_active, moderately_active, very_active, extra_active")
    occupation_type: Optional[str] = None
    sport_name: Optional[str] = None
    sport_position: Optional[str] = None
    training_preferences: Dict[str, Any] = Field(default_factory=dict)
    goal: Optional[GoalSchema] = None


class AthleteProfileUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=13, le=100)
    sex: Optional[str] = None
    height_cm: Optional[float] = Field(None, gt=50, lt=300)
    current_weight_kg: Optional[float] = Field(None, gt=20, lt=500)
    timezone: Optional[str] = None
    training_experience_years: Optional[float] = Field(None, ge=0.0, le=70.0)
    activity_level: Optional[str] = None
    occupation_type: Optional[str] = None
    sport_name: Optional[str] = None
    sport_position: Optional[str] = None
    training_preferences: Optional[Dict[str, Any]] = None
    goal: Optional[GoalSchema] = None


class AthleteProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    age: int
    sex: str
    height_cm: float
    current_weight_kg: float
    timezone: str
    training_experience_years: float
    activity_level: str
    occupation_type: Optional[str] = None
    sport_name: Optional[str] = None
    sport_position: Optional[str] = None
    training_preferences: Dict[str, Any]
    goals: List[GoalSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class OnboardingRequest(BaseModel):
    # Personal & Biometrics
    age: int = Field(..., ge=13, le=100)
    sex: str = Field(..., description="male, female, or other")
    height_cm: float = Field(..., gt=50, lt=300)
    current_weight_kg: float = Field(..., gt=20, lt=500)
    timezone: str = Field(default="Asia/Kolkata")
    occupation_type: Optional[str] = "Desk / Professional"
    activity_level: str = Field(default="moderately_active")

    # Goals & Sport
    primary_goal: str = Field(default="muscle_gain")
    target_weight_kg: Optional[float] = Field(None, gt=20, lt=500)
    target_date: Optional[str] = None
    sport_name: Optional[str] = None
    sport_position: Optional[str] = None

    # Training Setup
    training_experience_years: float = Field(default=1.0, ge=0.0, le=70.0)
    days_per_week: int = Field(default=4, ge=1, le=7)
    preferred_days: List[str] = Field(default_factory=lambda: ["Mon", "Tue", "Thu", "Fri"])
    session_duration_minutes: int = Field(default=60, ge=20, le=180)
    available_equipment: List[str] = Field(default_factory=lambda: ["bodyweight", "dumbbell", "barbell"])

    # Mandatory Pre-Diet Nutrition & Budget Context
    dietary_type: str = Field(default="omnivore", description="vegetarian, eggetarian, vegan, omnivore, jain, halal")
    weekly_food_budget_inr: float = Field(default=2500.0, ge=200.0, le=100000.0)
    currency_code: str = Field(default="INR")
    meals_per_day: int = Field(default=4, ge=1, le=8)
    staple_foods: List[str] = Field(default_factory=list)
    liked_foods: List[str] = Field(default_factory=list)
    disliked_foods: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    avoided_foods: List[str] = Field(default_factory=list)
