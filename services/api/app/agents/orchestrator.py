from app.agents.base import BaseAgent, AgentInputEnvelope, AgentOutputEnvelope


class CoachOrchestrator(BaseAgent):
    @property
    def agent_name(self) -> str:
        return "CoachOrchestrator"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        # Phase 1 Stub
        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={"status": "initialized", "target_spokes": []},
            explanation="Coach Orchestrator interface established (Phase 1). Full multi-agent routing will be activated in Phase 3.",
            validation_passed=True,
            is_fallback=True
        )
