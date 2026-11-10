from app.agents.base import BaseAgent, AgentInputEnvelope, AgentOutputEnvelope


class TrainingAgent(BaseAgent):
    @property
    def agent_name(self) -> str:
        return "TrainingAgent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={"status": "initialized", "workout_plan": None},
            explanation="Training Agent interface established (Phase 1). AI program generation will be implemented in Phase 3.",
            validation_passed=True,
            is_fallback=True
        )
