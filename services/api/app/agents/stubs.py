from app.agents.base import BaseAgent, AgentInputEnvelope, AgentOutputEnvelope


class RecoveryAgent(BaseAgent):
    @property
    def agent_name(self) -> str:
        return "RecoveryAgent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={"status": "initialized", "readiness_score": None},
            explanation="Recovery Agent interface established (Phase 1). Readiness calculations will be activated in Phase 4.",
            validation_passed=True,
            is_fallback=True
        )


class ProgressAgent(BaseAgent):
    @property
    def agent_name(self) -> str:
        return "ProgressAgent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={"status": "initialized", "trend_analysis": None},
            explanation="Progress Agent interface established (Phase 1). Trend tracking will be activated in Phase 5.",
            validation_passed=True,
            is_fallback=True
        )


class BodyAnalysisAgent(BaseAgent):
    @property
    def agent_name(self) -> str:
        return "BodyAnalysisAgent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={
                "status": "initialized",
                "disclaimer": "Visual body estimates are qualitative and subject to lighting/angle uncertainty."
            },
            explanation="Body Analysis Agent interface established (Phase 1). Progress photo vision pipeline will be implemented in Phase 4.",
            validation_passed=True,
            is_fallback=True
        )


class SafetyValidationComponent(BaseAgent):
    @property
    def agent_name(self) -> str:
        return "SafetyValidationComponent"

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={"status": "initialized", "violations": []},
            explanation="Safety Validation component interface established (Phase 1). Hard boundary checks will be hardened in Phase 8.",
            validation_passed=True,
            is_fallback=True
        )
