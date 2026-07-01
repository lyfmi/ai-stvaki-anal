import base64
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.services.ai.models import resolve_model, text_model_fallback_chain
from app.services.ai.providers.groq_errors import GroqApiError
from app.services.ai.providers.json_utils import parse_ai_json

logger = logging.getLogger(__name__)


class GroqClient:
    """OpenAI-compatible Groq API client."""

    def __init__(self, model: str | None = None) -> None:
        self.base_url = settings.groq_api_base.rstrip("/")
        self.api_key = settings.groq_api_key
        self.model = model

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.2,
        json_mode: bool = True,
        images: list[bytes] | None = None,
        image_mime: str = "image/jpeg",
    ) -> tuple[str | None, str, str]:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        token_limit = max_tokens if max_tokens is not None else settings.groq_max_tokens

        if images:
            messages = _inject_images(messages, images, image_mime)
            models_to_try = [resolve_model(model or self.model, vision=True)]
        else:
            models_to_try = text_model_fallback_chain(model or self.model)

        last_error: GroqApiError | None = None
        async with httpx.AsyncClient(timeout=120.0) as client:
            for use_model in models_to_try:
                payload: dict[str, Any] = {
                    "model": use_model,
                    "messages": messages,
                    "max_tokens": token_limit,
                    "temperature": temperature,
                }
                if json_mode:
                    payload["response_format"] = {"type": "json_object"}

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if response.status_code == 429:
                    detail = response.text[:500]
                    last_error = GroqApiError(response.status_code, detail)
                    logger.warning("Groq rate limit for %s, trying next model", use_model)
                    continue
                body_lower = response.text.lower()
                if response.status_code == 400 and "json_validate" in body_lower:
                    detail = response.text[:500]
                    last_error = GroqApiError(response.status_code, detail)
                    logger.warning("Groq JSON mode failed for %s, trying next model", use_model)
                    continue
                if response.status_code == 404 and (
                    "model_not_found" in body_lower or "does not exist" in body_lower
                ):
                    detail = response.text[:500]
                    last_error = GroqApiError(response.status_code, detail)
                    logger.warning("Groq model unavailable %s, trying next model", use_model)
                    continue
                if response.status_code >= 400:
                    detail = response.text[:500]
                    raise GroqApiError(response.status_code, detail)

                data = response.json()
                if error := data.get("error"):
                    message = error.get("message") if isinstance(error, dict) else str(error)
                    raise GroqApiError(500, str(message))

                choices = data.get("choices") or []
                if not choices:
                    raise RuntimeError("Groq API returned no choices")

                choice = choices[0]
                message = choice.get("message") or {}
                content = message.get("content")
                finish_reason = str(choice.get("finish_reason") or "stop")
                model_used = str(data.get("model") or use_model)

                content_text = content.strip() if isinstance(content, str) and content.strip() else None
                if not content_text:
                    raise RuntimeError(f"Empty AI response (finish_reason={finish_reason})")

                if finish_reason == "length":
                    logger.warning(
                        "Groq response truncated at %s tokens (model=%s)", token_limit, model_used
                    )

                if use_model != models_to_try[0]:
                    logger.info("Groq fallback succeeded with model %s", model_used)
                return content_text, model_used, finish_reason

        if last_error is not None:
            raise last_error
        raise RuntimeError("Groq API request failed")

    async def vision_json(
        self,
        image_bytes: bytes,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
        mime_type: str = "image/jpeg",
        max_tokens: int | None = None,
    ) -> dict:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        content, _, finish_reason = await self.chat_completion(
            messages,
            model=model,
            max_tokens=max_tokens,
            images=[image_bytes],
            image_mime=mime_type,
        )
        data = parse_ai_json(content)
        data["_finish_reason"] = finish_reason
        return data

    async def text_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        content, _, finish_reason = await self.chat_completion(
            messages, model=model, max_tokens=max_tokens
        )
        data = parse_ai_json(content)
        data["_finish_reason"] = finish_reason
        return data


def _inject_images(
    messages: list[dict[str, Any]],
    images: list[bytes],
    mime_type: str,
) -> list[dict[str, Any]]:
    """Attach images[] to the last user message (Groq multimodal format)."""
    cloned = [dict(m) for m in messages]
    user_idx = None
    for idx in range(len(cloned) - 1, -1, -1):
        if cloned[idx].get("role") == "user":
            user_idx = idx
            break
    if user_idx is None:
        cloned.append({"role": "user", "content": ""})
        user_idx = len(cloned) - 1

    raw = cloned[user_idx].get("content")
    text = raw if isinstance(raw, str) else ""
    parts: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for image_bytes in images[:5]:
        b64 = base64.b64encode(image_bytes).decode()
        parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64}"},
            }
        )
    cloned[user_idx]["content"] = parts
    return cloned
