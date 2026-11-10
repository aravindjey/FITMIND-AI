from fastapi import APIRouter

from app.api.v1.endpoints import health, auth, athlete, audit

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(athlete.router, prefix="/athlete", tags=["Athlete Profile"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
