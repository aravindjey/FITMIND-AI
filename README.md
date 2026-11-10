# AI Fitness Coach

A production-grade, personalized **AI Fitness & Athletic Coaching Platform** built with **Next.js 14**, **FastAPI**, **SQLAlchemy 2.x (Async)**, **Alembic**, and **PostgreSQL / SQLite**.

## Core Architecture Principles
1. **Authoritative Database State:** The relational database is the single source of truth for all athlete profiles, workouts, nutrition plans, food logs, measurements, check-ins, and personal records. LLMs are never trusted as persistent memory.
2. **Deterministic Mathematical Engines:** BMR (Mifflin-St Jeor), TDEE, macronutrient targets, 1RM estimation (Epley/Brzycki), progressive overload prescriptions, 7-day EMA weight trends, and safety guardrails are computed by pure deterministic Python functions (`services/api/app/engines/`).
3. **Eight Specialized AI Components + Central Orchestrator:** Coordinated by `CoachOrchestrator` (`services/api/app/agents/`) with provider-independent LLM/Vision abstractions (`services/api/app/ai/`) and transparent development fallbacks (`is_fallback=True`).
4. **Multi-Tenant Data Isolation:** Every database query is strictly scoped to the authenticated user (`current_user.id`) via Argon2id + JWT authentication (`HTTP-Only` cookie + `Bearer` token support).

---

## Repository Structure

```text
ai-fitness-coach/
├── ARCHITECTURE.md              # Full system architecture blueprint
├── AGENTS.md                    # Multi-agent & anti-hallucination specification
├── docker-compose.yml           # Local PostgreSQL 16 + API + Web stack
├── .env.example                 # Environment configuration template
├── docs/                        # Project master plan, status report, ADRs & logs
├── apps/
│   └── web/                     # Next.js 14 (React 18, TypeScript, Tailwind CSS)
└── services/
    └── api/                     # FastAPI Backend, SQLAlchemy Models, Alembic, Pytest
```

---

## Quick Start (Local Development)

### 1. Backend Setup (`services/api`)
```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run Alembic database migrations
PYTHONPATH=. alembic upgrade head

# Start FastAPI server on http://localhost:8000
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup (`apps/web`)
```bash
cd apps/web
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

### 3. Running Automated Tests
```bash
# Backend unit, integration & isolation tests
cd services/api
PYTHONPATH=. .venv/bin/pytest -v

# Frontend production build & TypeScript check
cd apps/web
npm run build
```

---

## Environment Variables
Copy `.env.example` to `.env` in the root or `services/api/.env`:
- `DATABASE_URL`: `postgresql+asyncpg://postgres:postgres@localhost:5432/ai_fitness_coach` (defaults to `sqlite+aiosqlite:///./ai_fitness_coach.db` in local dev)
- `SECRET_KEY`: 32+ character secret key for signing JWTs
- `LLM_PROVIDER`: `mock` | `openai` | `anthropic` | `gemini` | `ollama`
- `PRIMARY_MODEL_NAME` / `VISION_MODEL_NAME`: Provider-specific model identifiers
- `DEFAULT_CURRENCY`: `INR`
