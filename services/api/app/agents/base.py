import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
import uuid
from pydantic import BaseModel, Field

from app.repositories.audit_repository import AuditRepository


class AgentInputEnvelope(BaseModel):
    user_id: uuid.UUID
    action: str
    context_data: Dict[str, Any] = Field(default_factory=dict)
    user_prompt: Optional[str] = None


class AgentOutputEnvelope(BaseModel):
    agent_name: str
    action: str
    result_data: Dict[str, Any]
    explanation: str
    validation_passed: bool = True
    is_fallback: bool = False
    execution_time_ms: int = 0
    errors: Optional[str] = None


class BaseAgent(ABC):
    @property
    @abstractmethod
    def agent_name(self) -> str:
        pass

    @abstractmethod
    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        pass


class AgentRunner:
    def __init__(self, audit_repo: Optional[AuditRepository] = None):
        self.audit_repo = audit_repo

    async def run_agent(self, agent: BaseAgent, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        start_time = time.time()
        try:
            output = await agent.process(envelope)
            execution_ms = int((time.time() - start_time) * 1000)
            output.execution_time_ms = execution_ms

            if self.audit_repo:
                await self.audit_repo.log_agent_execution(
                    user_id=envelope.user_id,
                    agent_name=agent.agent_name,
                    action=envelope.action,
                    input_snapshot=envelope.model_dump(mode="json"),
                    output_snapshot=output.model_dump(mode="json"),
                    validation_passed=output.validation_passed,
                    execution_time_ms=execution_ms,
                    error_info=output.errors
                )
            return output
        except Exception as e:
            execution_ms = int((time.time() - start_time) * 1000)
            error_output = AgentOutputEnvelope(
                agent_name=agent.agent_name,
                action=envelope.action,
                result_data={},
                explanation="Agent execution encountered an unhandled exception.",
                validation_passed=False,
                execution_time_ms=execution_ms,
                errors=str(e)
            )
            if self.audit_repo:
                await self.audit_repo.log_agent_execution(
                    user_id=envelope.user_id,
                    agent_name=agent.agent_name,
                    action=envelope.action,
                    input_snapshot=envelope.model_dump(mode="json"),
                    output_snapshot=error_output.model_dump(mode="json"),
                    validation_passed=False,
                    execution_time_ms=execution_ms,
                    error_info=str(e)
                )
            return error_output
