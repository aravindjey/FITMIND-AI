import pytest
import uuid
from pydantic import BaseModel
from app.ai.factory import get_llm_provider, get_vision_provider
from app.ai.fallback import DevelopmentFallbackProvider
from app.agents.base import AgentInputEnvelope, AgentRunner
from app.agents.orchestrator import CoachOrchestrator


class MockSchema(BaseModel):
    message: str = "test"
    count: int = 1


@pytest.mark.asyncio
async def test_ai_provider_fallback_transparency():
    provider = get_llm_provider()
    response = await provider.generate_structured_output(
        prompt="Test prompt",
        system_instruction="System prompt",
        response_schema=MockSchema
    )

    assert response.is_fallback is True
    assert response.provider_name == "development_fallback"
    assert "FALLBACK" in response.metadata["notice"]


@pytest.mark.asyncio
async def test_vision_provider_fallback():
    provider = get_vision_provider()
    response = await provider.analyze_image_structured(
        image_bytes=b"fake_image_bytes",
        prompt="Analyze photo",
        response_schema=MockSchema
    )

    assert response.is_fallback is True
    assert response.provider_name == "development_fallback_vision"


@pytest.mark.asyncio
async def test_agent_runner_execution():
    orchestrator = CoachOrchestrator()
    runner = AgentRunner(audit_repo=None)

    envelope = AgentInputEnvelope(
        user_id=uuid.uuid4(),
        action="orchestrate",
        user_prompt="Help me train"
    )

    result = await runner.run_agent(orchestrator, envelope)
    assert result.agent_name == "CoachOrchestrator"
    assert result.validation_passed is True
    assert result.execution_time_ms >= 0
