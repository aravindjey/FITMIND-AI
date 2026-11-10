import time
import json
import base64
import logging
from typing import Type, TypeVar
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.ai.base import BaseLLMProvider, BaseVisionProvider, StructuredAIResponse
from app.ai.fallback import DevelopmentFallbackProvider

logger = logging.getLogger("ai_fitness_coach.ai")
T = TypeVar("T", bound=BaseModel)


class OpenAICompatibleProvider(BaseLLMProvider, BaseVisionProvider):
    """Provider adapter for OpenAI / Ollama / OpenAI-compatible JSON endpoints via httpx."""

    def __init__(self, api_key: str, model_name: str, vision_model_name: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model_name = model_name
        self.vision_model_name = vision_model_name
        self.base_url = base_url.rstrip("/")

    async def generate_structured_output(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Type[T],
        temperature: float = 0.2
    ) -> StructuredAIResponse[T]:
        start_time = time.time()
        schema_json = json.dumps(response_schema.model_json_schema())
        full_system = (
            f"{system_instruction}\n\n"
            f"IMPORTANT: Respond ONLY with valid JSON conforming to this schema:\n{schema_json}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": full_system},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                body = resp.json()
                raw_content = body["choices"][0]["message"]["content"]
                parsed = response_schema.model_validate_json(raw_content)
                execution_ms = int((time.time() - start_time) * 1000)
                return StructuredAIResponse(
                    data=parsed,
                    provider_name="openai",
                    model_name=self.model_name,
                    is_fallback=False,
                    execution_time_ms=execution_ms,
                )
        except Exception as e:
            logger.warning(f"OpenAI provider call failed ({e}); using transparent DevelopmentFallbackProvider.")
            fb = DevelopmentFallbackProvider(reason=f"Provider API error: {str(e)}")
            return await fb.generate_structured_output(prompt, system_instruction, response_schema, temperature)

    async def analyze_image_structured(
        self,
        image_bytes: bytes,
        prompt: str,
        response_schema: Type[T]
    ) -> StructuredAIResponse[T]:
        start_time = time.time()
        schema_json = json.dumps(response_schema.model_json_schema())
        b64_img = base64.b64encode(image_bytes).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.vision_model_name,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{prompt}\n\nReturn JSON matching:\n{schema_json}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}},
                    ],
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                body = resp.json()
                raw_content = body["choices"][0]["message"]["content"]
                parsed = response_schema.model_validate_json(raw_content)
                execution_ms = int((time.time() - start_time) * 1000)
                return StructuredAIResponse(
                    data=parsed,
                    provider_name="openai_vision",
                    model_name=self.vision_model_name,
                    is_fallback=False,
                    execution_time_ms=execution_ms,
                )
        except Exception as e:
            logger.warning(f"Vision provider call failed ({e}); using transparent DevelopmentFallbackProvider.")
            fb = DevelopmentFallbackProvider(reason=f"Vision API error: {str(e)}")
            return await fb.analyze_image_structured(image_bytes, prompt, response_schema)


class GeminiProvider(BaseLLMProvider, BaseVisionProvider):
    """Provider adapter for Google Gemini REST API via httpx."""

    def __init__(self, api_key: str, model_name: str, vision_model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.vision_model_name = vision_model_name

    async def generate_structured_output(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: Type[T],
        temperature: float = 0.2
    ) -> StructuredAIResponse[T]:
        start_time = time.time()
        schema_json = json.dumps(response_schema.model_json_schema())
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_instruction}\n\n{prompt}\n\nRespond strictly in JSON matching schema:\n{schema_json}"}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            }
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                body = resp.json()
                text_out = body["candidates"][0]["content"]["parts"][0]["text"]
                parsed = response_schema.model_validate_json(text_out)
                execution_ms = int((time.time() - start_time) * 1000)
                return StructuredAIResponse(
                    data=parsed,
                    provider_name="gemini",
                    model_name=self.model_name,
                    is_fallback=False,
                    execution_time_ms=execution_ms,
                )
        except Exception as e:
            fb = DevelopmentFallbackProvider(reason=f"Gemini API error ({type(e).__name__})")
            return await fb.generate_structured_output(prompt, system_instruction, response_schema, temperature)

    async def analyze_image_structured(
        self,
        image_bytes: bytes,
        prompt: str,
        response_schema: Type[T]
    ) -> StructuredAIResponse[T]:
        start_time = time.time()
        schema_json = json.dumps(response_schema.model_json_schema())
        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.vision_model_name}:generateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"{prompt}\n\nRespond strictly in JSON matching schema:\n{schema_json}"},
                        {"inlineData": {"mimeType": "image/jpeg", "data": b64_img}},
                    ]
                }
            ],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                body = resp.json()
                text_out = body["candidates"][0]["content"]["parts"][0]["text"]
                parsed = response_schema.model_validate_json(text_out)
                execution_ms = int((time.time() - start_time) * 1000)
                return StructuredAIResponse(
                    data=parsed,
                    provider_name="gemini_vision",
                    model_name=self.vision_model_name,
                    is_fallback=False,
                    execution_time_ms=execution_ms,
                )
        except Exception as e:
            fb = DevelopmentFallbackProvider(reason=f"Gemini Vision API error ({type(e).__name__})")
            return await fb.analyze_image_structured(image_bytes, prompt, response_schema)


def get_llm_provider() -> BaseLLMProvider:
    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAICompatibleProvider(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.PRIMARY_MODEL_NAME,
            vision_model_name=settings.VISION_MODEL_NAME,
        )
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.PRIMARY_MODEL_NAME,
            vision_model_name=settings.VISION_MODEL_NAME,
        )

    return DevelopmentFallbackProvider(
        reason=f"Provider '{provider}' unconfigured or running in deterministic development fallback mode"
    )


def get_vision_provider() -> BaseVisionProvider:
    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAICompatibleProvider(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.PRIMARY_MODEL_NAME,
            vision_model_name=settings.VISION_MODEL_NAME,
        )
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.PRIMARY_MODEL_NAME,
            vision_model_name=settings.VISION_MODEL_NAME,
        )

    return DevelopmentFallbackProvider(
        reason="Vision provider unconfigured or running in deterministic development fallback mode"
    )
