from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic, Optional, Any, Dict
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StructuredAIResponse(BaseModel, Generic[T]):
    data: T
    provider_name: str
    model_name: str
    is_fallback: bool = False
    fallback_reason: Optional[str] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = {}


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_structured_output(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Type[T],
        temperature: float = 0.2
    ) -> StructuredAIResponse[T]:
        """Generate structured response matching pydantic schema."""
        pass


class BaseVisionProvider(ABC):
    @abstractmethod
    async def analyze_image_structured(
        self,
        image_bytes: bytes,
        prompt: str,
        response_schema: Type[T]
    ) -> StructuredAIResponse[T]:
        """Analyze visual content and return structured response."""
        pass
