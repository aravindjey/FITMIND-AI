import os
from typing import List, Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_SECRET_KEY = "dev-secret-key-change-this-in-production-min-32-chars"


class Settings(BaseSettings):
    PROJECT_NAME: str = "FITMIND AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = DEFAULT_DEV_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    AUTH_RATE_LIMIT_MAX_ATTEMPTS: int = 15
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./ai_fitness_coach.db",
        description="Async SQLAlchemy database URL"
    )
    ALLOW_SQLITE_IN_PRODUCTION: bool = False

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

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

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.ENVIRONMENT.lower() == "production":
            if self.SECRET_KEY == DEFAULT_DEV_SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "CRITICAL SECURITY ERROR: Production environment requires a strong custom SECRET_KEY "
                    "(minimum 32 characters) and cannot use the default development secret key."
                )
            if self.DATABASE_URL.startswith("sqlite") and not self.ALLOW_SQLITE_IN_PRODUCTION:
                raise ValueError(
                    "CRITICAL CONFIGURATION ERROR: Production environment cannot silently fall back to SQLite. "
                    "Configure a PostgreSQL DATABASE_URL or explicitly set ALLOW_SQLITE_IN_PRODUCTION=true."
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
