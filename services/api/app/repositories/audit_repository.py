from typing import Dict, Any, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.audit import AgentAuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_agent_execution(
        self,
        user_id: uuid.UUID,
        agent_name: str,
        action: str,
        input_snapshot: Dict[str, Any],
        output_snapshot: Dict[str, Any],
        validation_passed: bool,
        execution_time_ms: int,
        error_info: Optional[str] = None
    ) -> AgentAuditLog:
        audit_log = AgentAuditLog(
            user_id=user_id,
            agent_name=agent_name,
            action=action,
            input_snapshot=input_snapshot,
            output_snapshot=output_snapshot,
            validation_passed=validation_passed,
            execution_time_ms=execution_time_ms,
            error_info=error_info
        )
        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        return audit_log

    async def get_logs_by_user(self, user_id: uuid.UUID, limit: int = 50):
        result = await self.session.execute(
            select(AgentAuditLog)
            .where(AgentAuditLog.user_id == user_id)
            .order_by(AgentAuditLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
