# AI Fitness Coach — Architectural & Engineering Decisions (`docs/DECISIONS.md`)

## ADR-001: Dual-Mode JWT Authentication (HTTP-Only Cookie + Bearer Header)
- **Context:** `ARCHITECTURE.md` specified HTTP-only cookies for XSS protection, while the initial Phase 1 API client used `Authorization: Bearer <token>` via `localStorage` and automated `pytest` tests passed `Bearer` headers.
- **Decision:** Support both mechanisms simultaneously in `get_current_user` (`services/api/app/api/deps.py`) and set an `HTTP-Only`, `SameSite=Lax` cookie (`access_token`) on `/auth/register` and `/auth/login` while also returning the token in the JSON response body.
- **Consequence:** Preserves 100% backward compatibility with all existing API tests and mobile/CLI clients while enabling secure cookie-based browser sessions (`credentials: 'include'`).

## ADR-002: Unified Relational Schema Without Duplicate Tables
- **Context:** Phase 1 migration `001_initial_schema.py` created 6 core tables (`users`, `athlete_profiles`, `goals`, `nutrition_profiles`, `check_ins`, `agent_audit_logs`). Phase 2 requires 14 additional domain entities (`food_preferences`, `exercises`, `workout_plans`, `workout_days`, `workout_exercises`, `workout_sessions`, `set_logs`, `nutrition_plans`, `food_items`, `meals`, `food_logs`, `body_measurements`, `progress_photos`, `personal_records`, `notifications`).
- **Decision:** Preserve `001_initial_schema.py` intact and add migration `002_complete_domain_schema.py` for the remaining tables and historical weight tracking.

## ADR-003: Single Orchestrated AI Client With Deterministic Domain Synthesis
- **Context:** The platform features 8 specialized AI components (`BodyAnalysisAgent`, `TrainingAgent`, `NutritionAgent`, `FitnessCoachingAgent`, `ProgressAgent`, `RecoveryAgent`, `SafetyValidationComponent`, `LifestyleHabitAgent`).
- **Decision:** All agents share a single provider-independent `BaseLLMProvider` / `BaseVisionProvider` factory (`services/api/app/ai/factory.py`). Mathematical computations (BMR, TDEE, macros, 1RM, EMA weight trends, volume, readiness scores, safety constraints) are executed by pure deterministic Python engines (`services/api/app/engines/`). When no external LLM API key is configured, agents use deterministic domain synthesis paired with `DevelopmentFallbackProvider` (`is_fallback=True`), ensuring the application is 100% functional offline/in development while remaining honest about fallback usage.

## ADR-004: Validated Indian & Global Nutritional Database (INR Default)
- **Context:** LLMs must never invent food calorie or macronutrient numbers, and the primary user context is India (`INR` / `₹`).
- **Decision:** Store verified nutritional values per 100g (both raw and cooked states where applicable) and estimated INR costs in the `food_items` database table, and compute meal plan macros and daily food logs deterministically from database records.
