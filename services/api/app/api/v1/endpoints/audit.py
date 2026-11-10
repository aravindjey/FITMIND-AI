from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.audit_repository import AuditRepository

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    agent_name: str
    action: str
    input_snapshot: Dict[str, Any]
    output_snapshot: Dict[str, Any]
    validation_passed: bool
    execution_time_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve audit logs for current user ONLY."""
    repo = AuditRepository(db)
    logs = await repo.get_logs_by_user(user_id=current_user.id)
    return [AuditLogResponse.model_validate(log) for log in logs]
