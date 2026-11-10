# FITMIND AI

> **INTELLIGENT FITNESS. SCIENCE-DRIVEN RESULTS.**

Production-grade, database-authoritative, AI-powered personalized Fitness & Athletic Coaching Platform built with **Next.js 14**, **FastAPI**, **SQLAlchemy 2.x Async**, **Alembic**, and a **Hub-and-Spoke Multi-Agent AI Architecture**.

---

## Core Capabilities

1. **Authoritative Athlete State (Never Chat-Memory Dependent)**
   - Persistent relational database storing athlete biometrics, historical body weight, 7-day Exponential Moving Average (EMA) trends, training preferences, equipment, injuries, dietary rules, allergies, and weekly food budgets in **Indian Rupees (₹ INR)**.
   - Every AI agent invocation is preceded by `AthleteStateHydrator`, which queries the database to build a deterministic context snapshot.

2. **Deterministic Physiological & Training Engines**
   - **Metabolic & Macro Engine (`nutrition_engine.py`)**: Mifflin-St Jeor BMR, activity-adjusted TDEE, protein ($1.6\text{–}2.2\text{ g/kg}$), essential dietary fat floors, carbohydrate periodization, and explicit calculation assumptions.
   - **Progressive Overload & Readiness Engine (`workout_engine.py`)**: Epley & Brzycki 1RM estimation, double progression + RPE autoregulation load prescriptions, session tonnage calculation, and a 0–100 Recovery Readiness Index.
   - **Safety Validation Gatekeeper (`safety_engine.py`)**: Configurable calorie floors, deficit caps, strict allergen exclusion, and session volume ceilings inspected before any AI plan is persisted.

3. **Hub-and-Spoke Multi-Agent AI System**
   - Coordinated by `CoachOrchestrator` with full execution auditing in `agent_run_logs`:
     - `TrainingAgent` (periodized 3/4/5+ day workout splits & biomechanical substitutions)
     - `NutritionAgent` (Indian & global staple meal plans respecting ₹ INR budgets and raw vs. cooked weights)
     - `FitnessCoachingAgent` (context-hydrated Q&A coaching)
     - `ProgressAgent` (7-day EMA weight & tonnage trajectory analysis)
     - `RecoveryAgent` (sleep, soreness, stress & training intensity autoregulation)
     - `BodyAnalysisAgent` (qualitative progress photo posture/physique assessment with explicit $\pm 4\text{–}6\%$ uncertainty disclaimers)
     - `LifestyleHabitAgent` (hydration, sleep hygiene, and NEAT step protocols)
     - `SafetyValidationComponent` (pre-persistence safety gatekeeper)
   - **Provider-Independent AI Configuration**: Supports OpenAI-compatible APIs (`LLM_PROVIDER=openai`), Google Gemini (`LLM_PROVIDER=gemini`), and a transparent `DevelopmentFallbackProvider` (`is_fallback=True`) when no external API key is configured.

---

## Repository Structure

```text
ai-fitness-coach/
├── apps/
│   └── web/                        # Next.js 14 (App Router, TypeScript, Tailwind CSS)
│       └── src/
│           ├── app/
│           │   ├── (auth)/         # /login, /register
│           │   └── (dashboard)/    # /dashboard, /onboarding, /profile, /workout,
│           │                       # /exercises, /nutrition, /ai-coach, /progress,
│           │                       # /check-in, /body-analysis, /reminders, /settings
│           ├── components/         # Sidebar, EmptyState
│           └── lib/                # Typed ApiClient (api-client.ts)
├── services/
│   └── api/                        # FastAPI + SQLAlchemy 2.x Async + Alembic
│       ├── alembic/                # Migrations 001_initial_schema & 002_complete_domain_schema
│       ├── app/
│       │   ├── agents/             # CoachOrchestrator & 8 specialized AI components
│       │   ├── ai/                 # Provider-independent LLM/Vision factory & Audit Runner
│       │   ├── api/v1/endpoints/   # auth, athlete, training, nutrition, coach, progress, audit
│       │   ├── core/               # Config & Argon2id/JWT security
│       │   ├── db/                 # Async session & declarative base
│       │   ├── engines/            # Deterministic nutrition, workout, and safety engines
│       │   ├── models/             # 21 SQLAlchemy ORM models
│       │   └── services/           # Seed catalogs (exercises & Indian foods) + StateHydrator
│       └── tests/                  # Pytest suite (unit, integration, tenant isolation)
├── docs/                           # Architecture, Master Plan, Status Report, Decisions, Dev Log
└── docker-compose.yml              # Local PostgreSQL, FastAPI, and Next.js orchestration
```

---

## Quick Start (Local Development)

### 1. Backend Setup (`services/api`)

```bash
cd services/api

# Activate virtual environment (or create with python3 -m venv .venv)
source .venv/bin/activate

# Apply Alembic database migrations (creates all 21 tables)
PYTHONPATH=. .venv/bin/alembic upgrade head

# Run automated test suite
PYTHONPATH=. .venv/bin/pytest -v

# Start FastAPI server on http://localhost:8000
PYTHONPATH=. .venv/bin/uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup (`apps/web`)

```bash
cd apps/web

# Install dependencies
npm install

# Verify production build
npm run build

# Start Next.js development server on http://localhost:3000
npm run dev
```

### 3. Environment Configuration (`.env`)

See `.env.example` at the repository root. Key variables:
- `DATABASE_URL`: Defaults to `sqlite+aiosqlite:///./ai_fitness_coach.db` for zero-config local execution, or set to `postgresql+asyncpg://postgres:postgres@localhost:5432/ai_fitness_coach` for PostgreSQL.
- `LLM_PROVIDER` / `VISION_PROVIDER`: Set to `openai` or `gemini` with `LLM_API_KEY` and `LLM_MODEL` to use live external AI models. When `LLM_API_KEY` is omitted, the platform automatically uses `DevelopmentFallbackProvider` (`is_fallback=True`) backed by the deterministic Python engines.
