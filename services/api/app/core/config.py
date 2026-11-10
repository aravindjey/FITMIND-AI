import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Fitness Coach"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-this-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./ai_fitness_coach.db",
        description="Async SQLAlchemy database URL"
    )

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # AI Configuration (Provider-Independent)
    LLM_PROVIDER: str = "mock"  # mock | openai | anthropic | gemini | ollama
    PRIMARY_MODEL_NAME: str = "gpt-4o-mini"
    VISION_MODEL_NAME: str = "gpt-4o-mini"

    # Optional AI Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Safety Rules
    SAFETY_MIN_BMR_MULTIPLIER: float = 1.0
    SAFETY_ABSOLUTE_MIN_CALORIES: int = 1200
    SAFETY_MAX_DAILY_DEFICIT_PERCENT: float = 0.25
    DEFAULT_CURRENCY: str = "INR"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
