import logging
from app.core.config import settings
from app.ai.base import BaseLLMProvider, BaseVisionProvider
from app.ai.fallback import DevelopmentFallbackProvider

logger = logging.getLogger("ai_fitness_coach.ai")


def get_llm_provider() -> BaseLLMProvider:
    provider = settings.LLM_PROVIDER.lower().strip()
    
    if provider == "openai" and settings.OPENAI_API_KEY:
        # Future Phase 3 OpenAI Provider integration
        pass
    elif provider == "anthropic" and settings.ANTHROPIC_API_KEY:
        # Future Phase 3 Anthropic Provider integration
        pass
    elif provider == "gemini" and settings.GEMINI_API_KEY:
        # Future Phase 3 Gemini Provider integration
        pass
        
    logger.info(f"Using AI Provider: {provider} (falling back to DevelopmentFallbackProvider if unconfigured)")
    return DevelopmentFallbackProvider(reason=f"Provider '{provider}' unconfigured or missing API key in Phase 1 setup")


def get_vision_provider() -> BaseVisionProvider:
    return DevelopmentFallbackProvider(reason="Vision provider initialized in Phase 1 development mode")
