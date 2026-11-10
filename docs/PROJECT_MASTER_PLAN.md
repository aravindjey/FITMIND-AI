# AI Fitness Coach — Project Master Plan (`docs/PROJECT_MASTER_PLAN.md`)

## 1. Objective
Complete the full-stack **AI Fitness Coach** platform across all 11 roadmap phases while preserving the existing working FastAPI + Next.js 14 modular monolith architecture.

---

## 2. Phase Execution Checklist

### Phase 1 — Foundation Remediation
- [x] Fix TypeScript syntax bug (`password: str` -> `password: string`) in `apps/web/src/lib/api-client.ts`.
- [x] Fix profile creation/update tracking (`hasProfile` state) in `apps/web/src/app/(dashboard)/profile/page.tsx`.
- [x] Reconcile JWT authentication to support both `HTTP-Only` cookies and `Authorization: Bearer` tokens (`services/api/app/api/deps.py`, `services/api/app/api/v1/endpoints/auth.py`).
- [ ] Install frontend `npm` dependencies and verify `next build`.
- [x] Verify backend `pytest` suite passes.
- [ ] Initialize Git repository (`git init`) and create root `README.md`.

### Phase 2 — Complete Database Schema & Onboarding
- [ ] Expand relational models (`services/api/app/models/`) and Alembic migration `002_complete_domain_schema.py` to cover all required tables:
  - `users`, `athlete_profiles`, `goals`, `nutrition_profiles` (existing)
  - `food_preferences`, `exercises`, `workout_plans`, `workout_days`, `workout_exercises`, `workout_sessions`, `set_logs`, `nutrition_plans`, `food_items`, `meals`, `food_logs`, `body_measurements`, `progress_photos`, `personal_records`, `check_ins`, `notifications`, `agent_audit_logs`.
- [ ] Implement historical body-weight recording whenever athlete weight is initialized or updated.
- [ ] Implement `AthleteStateHydrator` (`services/api/app/services/state_hydrator.py`) to retrieve authoritative athlete context from the database.
- [ ] Implement `POST /api/v1/athlete/onboarding` and `GET /api/v1/athlete/state` endpoints.
- [ ] Build multi-step `/onboarding` frontend wizard (personal info, height/weight, experience, goals, training preferences, available equipment, dietary preferences, allergies, staple foods, INR food budget, activity level).

### Phase 3 — Workout Management Subsystem
- [ ] Seed curated exercise library (`exercises` table: barbell, dumbbell, machine, bodyweight, cable movements across squat, hinge, push, pull, carry, isolation patterns).
- [ ] Implement deterministic progressive overload, volume analysis, 1RM estimation, and exercise substitution logic (`services/api/app/engines/workout_engine.py`).
- [ ] Implement workout endpoints (`/api/v1/training/exercises`, `/api/v1/training/generate-plan`, `/api/v1/training/active-plan`, `/api/v1/training/sessions`, `/api/v1/training/history`, `/api/v1/training/prs`, `/api/v1/training/substitute`).
- [ ] Build Workout Planner, Workout Logger, and Exercise Library frontend views.

### Phase 4 — Nutrition Management Subsystem
- [ ] Implement deterministic BMR (Mifflin-St Jeor), TDEE, calorie target, and macronutrient target calculation engine (`services/api/app/engines/nutrition_engine.py`) with explicit calculation assumptions.
- [ ] Seed validated Indian & global food database (`food_items` table with raw/cooked states, per-100g macros, serving sizes, and estimated INR cost).
- [ ] Implement nutrition endpoints (`/api/v1/nutrition/targets`, `/api/v1/nutrition/generate-plan`, `/api/v1/nutrition/active-plan`, `/api/v1/nutrition/foods`, `/api/v1/nutrition/logs`, `/api/v1/nutrition/summary`, `/api/v1/nutrition/substitute`).
- [ ] Build Nutrition Planner and Food Tracker frontend views.

### Phase 5 — Eight Specialized AI Components
- [ ] Implement provider-independent LLM & Vision adapters (`OpenAI`, `Anthropic`, `Gemini`, plus transparent `DevelopmentFallbackProvider`) in `services/api/app/ai/`.
- [ ] Implement all 8 specialized components in `services/api/app/agents/`:
  1. `BodyAnalysisAgent` (vision analysis, measurement interpretation, explicit uncertainty)
  2. `TrainingAgent` (Workout Planning Agent)
  3. `NutritionAgent` (INR budget & dietary restriction-aware meal planning)
  4. `FitnessCoachingAgent` (natural-language Q&A grounded in athlete context)
  5. `ProgressAgent` (weight trends, measurement deltas, strength progression)
  6. `RecoveryAgent` (sleep, fatigue, soreness readiness evaluation)
  7. `SafetyValidationComponent` (configurable calorie floors, deficit caps, allergy & volume checks)
  8. `LifestyleHabitAgent` (daily check-ins, consistency streaks, reminder coordination)

### Phase 6 — Central AI Orchestrator & Persistent Memory
- [ ] Implement `CoachOrchestrator` routing, context hydration via `AthleteStateHydrator`, specialist coordination, safety validation gate, and `AgentAuditLog` persistence.
- [ ] Implement `/api/v1/coach/chat` and `/api/v1/coach/recommendations` endpoints and `/ai-coach` frontend interface.

### Phase 7 — Progress, Recovery & Lifestyle
- [ ] Implement body-weight history, 7-day EMA trends, body measurements CRUD, strength progression analytics, daily check-ins, recovery readiness dashboard, and deterministic reminder scheduling (`/api/v1/progress/*`, `/api/v1/check-ins/*`, `/api/v1/recovery/*`, `/api/v1/notifications/*`).

### Phase 8 — Body Analysis & Progress Photos
- [ ] Implement secure photo upload with file validation, local/object storage abstraction, photo history, measurement comparison, and `BodyAnalysisAgent` vision integration (`/api/v1/body-analysis/*`).

### Phase 9 — Complete Frontend Integration
- [ ] Build and connect all principal frontend pages (`/onboarding`, `/dashboard`, `/profile`, `/ai-coach`, `/workout`, `/exercises`, `/nutrition`, `/progress`, `/body-analysis`, `/recovery`, `/check-in`, `/reminders`, `/settings`).

### Phase 10 & 11 — Testing, Security Verification & Deployment Readiness
- [ ] Comprehensive backend unit & integration test suite (`pytest`) covering all modules and cross-user isolation.
- [ ] End-to-end user journey verification and production deployment documentation.
