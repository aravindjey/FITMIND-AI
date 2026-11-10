from fastapi import APIRouter

from app.api.v1.endpoints import health, auth, athlete, audit, training, nutrition, coach, progress

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(athlete.router, prefix="/athlete", tags=["Athlete Profile & Onboarding"])
api_router.include_router(training.router, prefix="/training", tags=["Workout Management"])
api_router.include_router(nutrition.router, prefix="/nutrition", tags=["Nutrition Management"])
api_router.include_router(coach.router, prefix="/coach", tags=["AI Coach Orchestrator"])
api_router.include_router(progress.router, prefix="/progress", tags=["Progress, Recovery & Reminders"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
