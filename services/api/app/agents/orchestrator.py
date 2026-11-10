from typing import Dict, Any, List
from app.agents.base import BaseAgent, AgentInputEnvelope, AgentOutputEnvelope
from app.agents.training_agent import TrainingAgent
from app.agents.nutrition_agent import NutritionAgent
from app.agents.stubs import (
    FitnessCoachingAgent,
    ProgressAgent,
    RecoveryAgent,
    BodyAnalysisAgent,
    SafetyValidationComponent,
    LifestyleHabitAgent,
)


class CoachOrchestrator(BaseAgent):
    """Central Hub-and-Spoke AI Orchestrator.
    Determines which specialist agent(s) to invoke based on user intent or action,
    executes them with hydrated database state, runs SafetyValidationComponent,
    and returns a unified structured response.
    """

    def __init__(self):
        self.training_agent = TrainingAgent()
        self.nutrition_agent = NutritionAgent()
        self.coaching_agent = FitnessCoachingAgent()
        self.progress_agent = ProgressAgent()
        self.recovery_agent = RecoveryAgent()
        self.body_agent = BodyAnalysisAgent()
        self.safety_agent = SafetyValidationComponent()
        self.lifestyle_agent = LifestyleHabitAgent()

    @property
    def agent_name(self) -> str:
        return "CoachOrchestrator"

    def _classify_intent(self, action: str, prompt: str) -> List[str]:
        if action == "generate_workout":
            return ["TrainingAgent", "SafetyValidationComponent"]
        if action == "generate_nutrition":
            return ["NutritionAgent", "SafetyValidationComponent"]
        if action == "analyze_body_photo":
            return ["BodyAnalysisAgent"]
        if action == "evaluate_recovery":
            return ["RecoveryAgent", "LifestyleHabitAgent"]
        if action == "analyze_progress":
            return ["ProgressAgent"]

        p_low = prompt.lower()
        spokes: List[str] = ["FitnessCoachingAgent"]
        if any(k in p_low for k in ("workout", "program", "split", "bench", "squat", "deadlift", "sets", "reps", "rpe")):
            spokes.append("ProgressAgent")
        if any(k in p_low for k in ("sleep", "tired", "sore", "fatigue", "recovery", "deload")):
            spokes.append("RecoveryAgent")
        if any(k in p_low for k in ("weight", "plateau", "progress", "trend", "gain", "loss")):
            if "ProgressAgent" not in spokes:
                spokes.append("ProgressAgent")
        if any(k in p_low for k in ("habit", "water", "hydration", "reminder", "consistent")):
            spokes.append("LifestyleHabitAgent")
        return spokes

    async def process(self, envelope: AgentInputEnvelope) -> AgentOutputEnvelope:
        prompt = envelope.user_prompt or ""
        target_spokes = self._classify_intent(envelope.action, prompt)

        spoke_outputs: Dict[str, Any] = {}
        explanations: List[str] = []
        any_fallback = False
        all_valid = True

        agent_map: Dict[str, BaseAgent] = {
            "TrainingAgent": self.training_agent,
            "NutritionAgent": self.nutrition_agent,
            "FitnessCoachingAgent": self.coaching_agent,
            "ProgressAgent": self.progress_agent,
            "RecoveryAgent": self.recovery_agent,
            "BodyAnalysisAgent": self.body_agent,
            "SafetyValidationComponent": self.safety_agent,
            "LifestyleHabitAgent": self.lifestyle_agent,
        }

        for spoke_name in target_spokes:
            spoke_agent = agent_map.get(spoke_name)
            if not spoke_agent:
                continue
            sub_out = await spoke_agent.process(envelope)
            spoke_outputs[spoke_name] = sub_out.result_data
            explanations.append(sub_out.explanation)
            if sub_out.is_fallback:
                any_fallback = True
            if not sub_out.validation_passed:
                all_valid = False

        primary_coaching = spoke_outputs.get("FitnessCoachingAgent") or {}
        combined_explanation = primary_coaching.get("answer") or " ".join(explanations)

        return AgentOutputEnvelope(
            agent_name=self.agent_name,
            action=envelope.action,
            result_data={
                "status": "completed",
                "target_spokes": target_spokes,
                "spoke_results": spoke_outputs,
                "answer": combined_explanation,
                "actionable_steps": primary_coaching.get("actionable_steps", []),
                "referenced_metrics": primary_coaching.get("referenced_metrics", []),
            },
            explanation=combined_explanation,
            validation_passed=all_valid,
            is_fallback=any_fallback,
        )
