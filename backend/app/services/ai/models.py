"""Groq model registry and validation."""
from __future__ import annotations

from app.core.config import settings

GROQ_ALLOWED_MODELS: frozenset[str] = frozenset(
    {
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "qwen/qwen3-32b",
        "moonshotai/kimi-k2-instruct",
        "llama-3.3-70b-versatile",
    }
)

GROQ_VISION_MODELS: frozenset[str] = frozenset({"meta-llama/llama-4-scout-17b-16e-instruct"})

# Separate TPD quotas per model — try lighter models when the default is rate-limited.
GROQ_TEXT_FALLBACK_CHAIN: tuple[str, ...] = (
    "qwen/qwen3-32b",
    "moonshotai/kimi-k2-instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.3-70b-versatile",
)


def text_model_fallback_chain(model: str | None = None) -> list[str]:
    primary = resolve_model(model, vision=False)
    chain = [primary]
    for candidate in GROQ_TEXT_FALLBACK_CHAIN:
        if candidate not in chain:
            chain.append(candidate)
    return chain


def resolve_model(model: str | None, *, vision: bool = False) -> str:
    requested = (model or "").strip()
    if requested:
        if requested not in GROQ_ALLOWED_MODELS:
            allowed = ", ".join(sorted(GROQ_ALLOWED_MODELS))
            raise ValueError(f"Unsupported model. Allowed: {allowed}")
        if vision and requested not in GROQ_VISION_MODELS:
            return settings.groq_vision_model
        return requested
    if vision:
        return settings.groq_vision_model
    return settings.groq_default_model
