from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.services.state_hydrator import AthleteStateHydrator
from app.agents.base import AgentInputEnvelope, AgentRunner
from app.agents.orchestrator import CoachOrchestrator

router = APIRouter()


class CoachChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)
    action: str = Field(default="chat")


@router.post("/chat")
async def coach_chat(
    chat_in: CoachChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Hydrates authoritative athlete context from the database, runs CoachOrchestrator
    and relevant specialist agents, validates recommendations, logs audit record, and returns response.
    """
    hydrator = AthleteStateHydrator(db)
    state = await hydrator.get_hydrated_state(current_user.id)

    orchestrator = CoachOrchestrator()
    runner = AgentRunner(audit_repo=AuditRepository(db))
    envelope = AgentInputEnvelope(
        user_id=current_user.id,
        action=chat_in.action,
        context_data=state,
        user_prompt=chat_in.message,
    )
    output = await runner.run_agent(orchestrator, envelope)

    return {
        "agent_name": output.agent_name,
        "action": output.action,
        "answer": output.result_data.get("answer") or output.explanation,
        "actionable_steps": output.result_data.get("actionable_steps", []),
        "referenced_metrics": output.result_data.get("referenced_metrics", []),
        "target_spokes": output.result_data.get("target_spokes", []),
        "spoke_results": output.result_data.get("spoke_results", {}),
        "validation_passed": output.validation_passed,
        "is_fallback": output.is_fallback,
        "execution_time_ms": output.execution_time_ms,
    }
