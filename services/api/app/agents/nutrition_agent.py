from app.agents.base import BaseAgent, AgentInputEnvelope, AgentOutputEnvelope


class NutritionAgent(BaseAgent):
    @property
    def agent_name(self) -> str:
        return "NutritionAgent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={"status": "initialized", "nutrition_plan": None},
            explanation="Nutrition Agent interface established (Phase 1). Meal plan synthesis will be implemented in Phase 3.",
            validation_passed=True,
            is_fallback=True
        )
