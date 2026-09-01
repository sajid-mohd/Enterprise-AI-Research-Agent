"""
LLM Provider abstraction.
Supports Groq (free), Gemini (free), and Anthropic.
Features multi-model fallback, exponential backoff, and robust JSON parsing.
"""
import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod

logger = logging.getLogger("research_agent.ai")

# Active reliable Groq models with JSON mode support
GROQ_ACTIVE_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
]


def _extract_json_candidate(text: str) -> str:
    """Extract a likely JSON string from arbitrary text (handles markdown fences and conversational wrappers)."""
    text = text.strip()
    # 1. Match code fences anywhere in text: ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()

    # 2. Match the outermost JSON object {...} or array [...]
    first_brace = text.find("{")
    first_bracket = text.find("[")

    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        last_brace = text.rfind("}")
        if last_brace > first_brace:
            return text[first_brace:last_brace + 1].strip()
    elif first_bracket != -1:
        last_bracket = text.rfind("]")
        if last_bracket > first_bracket:
            return text[first_bracket:last_bracket + 1].strip()

    return text


def parse_json_response(text: str) -> dict | list:
    """
    Robustly parse JSON from LLM output.
    Handles:
    - Direct JSON
    - Markdown code fences (```json ... ```)
    - Conversational pre/post-ambles ('Here is the JSON: ... Hope this helps!')
    - Trailing commas before closing braces/brackets
    """
    if not text or not text.strip():
        return {}

    candidate = _extract_json_candidate(text)

    # Attempt 1: Direct standard parse
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Attempt 2: Non-strict mode
    try:
        return json.loads(candidate, strict=False)
    except json.JSONDecodeError:
        pass

    # Attempt 3: Remove trailing commas: e.g. {"a": 1,} -> {"a": 1}
    fixed = re.sub(r",\s*([\]}])", r"\1", candidate)
    try:
        return json.loads(fixed, strict=False)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed completely: %s | Extracted candidate: %.200s", exc, candidate)
        return {}


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        ...


class GroqProvider(LLMProvider):
    """Groq — high-speed inference with active model fallback."""

    def __init__(self, api_key: str, model: str = "qwen/qwen3.8-27b"):
        self.api_key = api_key
        # Sanitize model string in case user wrote MODEL_VAR=model_name in .env
        clean_m = model.split("=")[-1].strip() if model else "qwen/qwen3.8-27b"
        self.model = clean_m or "qwen/qwen3.8-27b"

    async def generate(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        from groq import AsyncGroq

        if not self.api_key or self.api_key.startswith("gsk_your_"):
            raise ValueError("Invalid Groq API key. Please configure a real GROQ_API_KEY in backend/.env.")

        client = AsyncGroq(api_key=self.api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Candidate models to try in order
        candidate_models = [self.model]
        for fallback_m in GROQ_ACTIVE_MODELS:
            if fallback_m not in candidate_models:
                candidate_models.append(fallback_m)

        last_error = None
        for current_model in candidate_models:
            kwargs: dict = {"model": current_model, "messages": messages, "max_tokens": 2048}
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            for attempt in range(2):
                try:
                    resp = await client.chat.completions.create(**kwargs)
                    content = resp.choices[0].message.content or ""
                    # If this model succeeded and was a fallback, adopt it
                    self.model = current_model
                    return content
                except Exception as exc:
                    err_msg = str(exc).lower()
                    last_error = exc
                    logger.warning("Groq model %s attempt %d failed: %s", current_model, attempt + 1, exc)
                    # If model is not found or decommissioned, break immediately to try next fallback model
                    if "model_not_found" in err_msg or "decommissioned" in err_msg or "does not exist" in err_msg or "404" in err_msg:
                        break
                    await asyncio.sleep(1.5 ** attempt)

        if last_error:
            raise last_error
        return ""


class GeminiProvider(LLMProvider):
    """Google Gemini — free tier."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        from google import genai
        from google.genai import types

        if not self.api_key:
            raise ValueError("Invalid Gemini API key. Please configure GEMINI_API_KEY in backend/.env.")

        client = genai.Client(api_key=self.api_key)

        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        if json_mode:
            full_prompt += "\n\nRespond ONLY with valid JSON. No explanation, no markdown fences."

        config = types.GenerateContentConfig(max_output_tokens=2048)

        for attempt in range(3):
            try:
                loop = asyncio.get_running_loop()
                resp = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model=self.model, contents=full_prompt, config=config
                    ),
                )
                return resp.text or ""
            except Exception as exc:
                logger.warning("Gemini attempt %d failed: %s", attempt + 1, exc)
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)
        return ""


class AnthropicProvider(LLMProvider):
    """Anthropic Claude — paid."""

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5"):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        import anthropic

        if not self.api_key:
            raise ValueError("Invalid Anthropic API key. Please configure ANTHROPIC_API_KEY in backend/.env.")

        client = anthropic.AsyncAnthropic(api_key=self.api_key)

        if json_mode:
            system = (system + "\n\nRespond ONLY with valid JSON. No explanation, no markdown fences.").strip()

        for attempt in range(3):
            try:
                msg = await client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=system or "You are a helpful research assistant.",
                    messages=[{"role": "user", "content": prompt}],
                )
                return msg.content[0].text if msg.content else ""
            except Exception as exc:
                logger.warning("Anthropic attempt %d failed: %s", attempt + 1, exc)
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)
        return ""


def get_llm_provider() -> LLMProvider:
    """Factory: instantiate provider from settings."""
    from app.core.config import settings

    provider = settings.PROVIDER.lower()
    model_override = settings.GENERATOR_MODEL or ""

    if provider == "groq":
        model = model_override or "qwen/qwen3.8-27b"
        return GroqProvider(api_key=settings.GROQ_API_KEY, model=model)
    elif provider == "gemini":
        model = model_override or "gemini-2.0-flash"
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=model)
    elif provider == "anthropic":
        model = model_override or "claude-haiku-4-5"
        return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY, model=model)
    else:
        raise ValueError(f"Unknown provider: {provider}. Choose: groq | gemini | anthropic")
