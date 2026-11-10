# AI Fitness Coach — Autonomous Engineering & Multi-Agent Specification (`AGENTS.md`)

## 1. System Mission
**AI Fitness Coach** is a production-grade, personalized fitness and athletic coaching web platform. Its core architectural invariant is:
> **The Relational Database is the single authoritative source of truth for all athlete records.**  
> Deterministic Python engines perform all mathematical, nutritional, volume, and progression calculations. Specialized AI components perform structured program synthesis, natural-language coaching, and qualitative interpretation subject to deterministic validation guardrails.

---

## 2. Anti-Hallucination & Execution Pipeline
Every AI-assisted operation follows a strict unidirectional pipeline:
1. **State Hydration (`AthleteStateHydrator`):** Fetches authoritative profile, goals, equipment, dietary preferences, recent workouts, weight history, personal records, and recovery metrics from PostgreSQL/SQLite.
2. **Deterministic Pre-Computation:** Calculates exact BMR, TDEE, macronutrient targets, 1RM estimates, weekly volume totals, and 7-day EMA weight trends in pure Python.
3. **Agent Execution (`AgentRunner`):** Invokes the target specialist agent through the provider-independent `BaseLLMProvider` / `BaseVisionProvider` interface using strict Pydantic v2 output schemas.
4. **Safety & Validation Gate (`SafetyValidationComponent`):** Checks proposed outputs against configurable BMR floors, deficit limits, allergy exclusions, equipment constraints, and volume caps.
5. **Audit & Persistence (`AuditRepository`):** Logs execution metadata (`is_fallback`, `validation_passed`, latency, snapshots) to `agent_audit_logs` and commits validated plans to the database.

---

## 3. Eight Specialized AI Components (`services/api/app/agents/`)

| # | Component | Class Name | Responsibility |
| :--- | :--- | :--- | :--- |
| **1** | **Body Analysis Agent** | `BodyAnalysisAgent` | Analyzes progress photos via `BaseVisionProvider`, compares body measurements, and outputs qualitative observations with explicit estimation uncertainty (never fake medical precision). |
| **2** | **Workout Planning Agent** | `TrainingAgent` | Synthesizes periodized workout plans (Strength, Powerlifting, Bodybuilding, General Fitness) respecting user equipment, schedule, PRs, and deterministic progressive overload rules. |
| **3** | **Nutrition Agent** | `NutritionAgent` | Generates personalized Indian and global meal plans matching deterministic BMR/TDEE macro targets, staple foods, dietary restrictions, allergies, and INR (`₹`) budgets. |
| **4** | **Fitness Coaching Agent** | `FitnessCoachingAgent` | Answers natural-language training, technique, and nutrition questions grounded in hydrated athlete state and sports-science principles. |
| **5** | **Progress Analysis Agent** | `ProgressAgent` | Evaluates 7-day EMA body-weight velocity, body measurement changes, 1RM progression, and weekly training volume. |
| **6** | **Recovery Agent** | `RecoveryAgent` | Evaluates sleep duration/quality, soreness, stress, and session RPE to compute a daily readiness score (1–100) and autoregulation recommendations. |
| **7** | **Safety & Validation Agent** | `SafetyValidationComponent` | Validates proposed workout and nutrition plans against configurable safety thresholds, allergy exclusions, and volume ceilings before database commit. |
| **8** | **Lifestyle & Habit Agent** | `LifestyleHabitAgent` | Processes daily check-ins, tracks hydration/sleep/adherence consistency streaks, and coordinates deterministic reminder schedules. |

Central coordination is handled by `CoachOrchestrator` (`services/api/app/agents/orchestrator.py`), which routes requests, hydrates context, invokes specialist components, validates outputs, and logs audits without instantiating redundant LLM clients.

---

## 4. Provider Independence & Fallback Transparency
- Configured via environment variables: `LLM_PROVIDER` (`mock`, `openai`, `anthropic`, `gemini`, `ollama`), `PRIMARY_MODEL_NAME`, `VISION_MODEL_NAME`.
- When external API credentials are not configured, `DevelopmentFallbackProvider` (`services/api/app/ai/fallback.py`) is used alongside deterministic rule-based synthesis and **explicitly flags every response with `is_fallback=True`** so fallback behavior is never misrepresented as live LLM inference.
