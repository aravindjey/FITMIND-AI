import time
import logging
from typing import Type, TypeVar
from pydantic import BaseModel

from app.ai.base import BaseLLMProvider, BaseVisionProvider, StructuredAIResponse

logger = logging.getLogger("ai_fitness_coach.ai")
T = TypeVar("T", bound=BaseModel)


class DevelopmentFallbackProvider(BaseLLMProvider, BaseVisionProvider):
    """Development fallback provider used when no API keys are provided.
    Explicitly flags all outputs as `is_fallback=True` to ensure transparency.
    """

    def __init__(self, reason: str = "No API key configured for requested provider"):
        self.reason = reason

    async def generate_structured_output(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Type[T],
        temperature: float = 0.2
    ) -> StructuredAIResponse[T]:
        start_time = time.time()
        logger.warning(f"[DEVELOPMENT FALLBACK ACTIVATED] {self.reason}")

        # Construct instance with default/mock values matching schema
        try:
            mock_data = response_schema.model_construct()
        except Exception:
            mock_data = response_schema.model_validate({})

        execution_ms = int((time.time() - start_time) * 1000)
        return StructuredAIResponse(
            data=mock_data,
            provider_name="development_fallback",
            model_name="mock-fallback-v1",
            is_fallback=True,
            fallback_reason=self.reason,
            execution_time_ms=execution_ms,
            metadata={"notice": "DEVELOPMENT FALLBACK - NOT REAL AI GENERATION"}
        )

    async def analyze_image_structured(
        self,
        image_bytes: bytes,
        prompt: str,
        response_schema: Type[T]
    ) -> StructuredAIResponse[T]:
        start_time = time.time()
        logger.warning(f"[DEVELOPMENT FALLBACK VISION ACTIVATED] {self.reason}")

        mock_data = response_schema.model_construct()
        execution_ms = int((time.time() - start_time) * 1000)

        return StructuredAIResponse(
            data=mock_data,
            provider_name="development_fallback_vision",
            model_name="mock-vision-fallback-v1",
            is_fallback=True,
            fallback_reason=self.reason,
            execution_time_ms=execution_ms,
            metadata={"notice": "DEVELOPMENT FALLBACK VISION - NOT REAL AI ANALYSIS"}
        )
