"""Single entry point for Groq chat completions, shared by the profile chat and resume generation."""

import logging
import os

from groq import Groq

logger = logging.getLogger(__name__)

# Fallback when GROQ_CHAT_MODEL is unset or no longer served (Groq retires models; llama-3.3-70b-versatile was).
DEFAULT_CHAT_MODEL = "openai/gpt-oss-120b"


class LLMUnavailable(RuntimeError):
    pass


def chat_completion(messages: list[dict], *, max_tokens: int, temperature: float = 0.2, json_mode: bool = False) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMUnavailable("GROQ_API_KEY is not configured")
    client = Groq(api_key=api_key)

    configured = (os.getenv("GROQ_CHAT_MODEL") or "").strip() or DEFAULT_CHAT_MODEL
    models = [configured] if configured == DEFAULT_CHAT_MODEL else [configured, DEFAULT_CHAT_MODEL]
    for index, model in enumerate(models):
        params = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if model.startswith("openai/gpt-oss"):
            # Reasoning models spend max_tokens on hidden reasoning first; keep it short so the answer isn't cut off.
            params["reasoning_effort"] = "low"
        if json_mode:
            params["response_format"] = {"type": "json_object"}
        try:
            completion = client.chat.completions.create(**params)
            return completion.choices[0].message.content or ""
        except Exception as exc:
            is_model_error = "model" in str(exc).lower()
            if index == len(models) - 1 or not is_model_error:
                raise
            logger.warning("Groq model %r unavailable, falling back to %r: %s", model, models[index + 1], exc)
    raise LLMUnavailable("No Groq model available")
