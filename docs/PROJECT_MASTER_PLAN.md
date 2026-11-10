# AI Fitness Coach — Master Development Plan

## 1. Architectural Vision
AI Fitness Coach is a production-grade, database-authoritative, AI-powered personalized fitness and athletic coaching platform.
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS (`apps/web`).
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.x Async, Pydantic 2.x, Alembic (`services/api`).
- **Database**: PostgreSQL (primary production target via `docker-compose.yml` or external URI) and SQLite (`sqlite+aiosqlite:///./ai_fitness_coach.db`) for zero-dependency local execution and testing.
- **Security**: Argon2id password hashing, JWT authentication supporting both `Authorization: Bearer` headers and `HttpOnly` cookies, and strict `user_id` tenant isolation across all 21 relational tables.
- **AI Architecture**: Provider-independent LLM & Vision abstraction (`OpenAICompatibleProvider`, `GeminiProvider`, and transparent `DevelopmentFallbackProvider`), `AthleteStateHydrator`, `CoachOrchestrator`, and 8 specialized agents (`BodyAnalysisAgent`, `TrainingAgent`, `NutritionAgent`, `FitnessCoachingAgent`, `ProgressAgent`, `RecoveryAgent`, `SafetyValidationComponent`, `LifestyleHabitAgent`) audited in `agent_run_logs`.

## 2. Phase Execution Status

| Phase | Milestone | Status | Verification |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Repository Re-Audit & Baseline | **COMPLETE** | Verified existing files, virtualenv, and Node environment |
| **Phase 1** | Immediate Remediation & Build Stability | **COMPLETE** | Fixed `api-client.ts`, unified JWT auth, initialized Git, `next build` passed |
| **Phase 2** | Complete Database Architecture | **COMPLETE** | Alembic migrations `001` + `002` create all 21 tables cleanly |
| **Phase 3** | Athlete Onboarding & Persistent Context | **COMPLETE** | `/athlete/onboarding`, `/athlete/state`, and `/onboarding` wizard verified |
| **Phase 4** | Workout Engine & Logging | **COMPLETE** | Periodized split generation, set/RPE logging, Epley 1RM PRs, double progression |
| **Phase 5** | Nutrition Engine & INR Food Budget | **COMPLETE** | Mifflin-St Jeor BMR/TDEE, Indian staple catalog, ₹ INR budget meal plans, raw/cooked logging |
| **Phase 6** | AI Agent Layer & Orchestration | **COMPLETE** | All 8 specialist agents + `CoachOrchestrator` + `SafetyValidationComponent` + audit logs |
| **Phase 7** | Progress, Recovery, Photos & Reminders | **COMPLETE** | 7-day EMA weight trend, 0–100 readiness index, qualitative photo analysis, reminders |
| **Phase 8** | Security & Tenant Isolation | **COMPLETE** | Verified cross-user isolation across all endpoints |
| **Phase 9** | Frontend Completion | **COMPLETE** | All 15 Next.js routes implemented and verified via `npm run build` |
| **Phase 10** | Full Testing & Verification | **COMPLETE** | 15/15 `pytest` tests passing + Alembic upgrade + Next.js static/dynamic build |
| **Phase 11** | Final Documentation & Git Commit | **COMPLETE** | All tracking documents and root `README.md` updated |
