import base64
import json
import logging
import re
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class NousClient:
    def __init__(self) -> None:
        self.base_url = settings.nous_api_base.rstrip("/")
        self.api_key = settings.nous_api_key
        self.model = settings.nous_model

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int = 8192,
        temperature: float = 0.2,
        json_mode: bool = True,
    ) -> str:
        if not self.api_key:
            raise RuntimeError("NOUS_API_KEY is not configured")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        if error := data.get("error"):
            message = error.get("message") if isinstance(error, dict) else str(error)
            raise RuntimeError(f"Nous API error: {message}")

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("Nous API returned no choices")

        choice = choices[0]
        message = choice.get("message") or {}
        raw = message.get("content")

        if not raw:
            reasoning = message.get("reasoning")
            if isinstance(reasoning, str) and reasoning.strip():
                raw = reasoning
            else:
                finish = choice.get("finish_reason", "unknown")
                raise RuntimeError(f"Empty AI response (finish_reason={finish})")

        if choice.get("finish_reason") == "length":
            logger.warning("AI response truncated at %s tokens", max_tokens)

        return raw

    async def vision_json(
        self,
        image_bytes: bytes,
        system_prompt: str,
        user_prompt: str,
        *,
        mime_type: str = "image/jpeg",
    ) -> dict:
        b64 = base64.b64encode(image_bytes).decode()
        content = [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
        ]
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]
        raw = await self.chat_completion(messages, max_tokens=8192)
        return parse_json_response(raw)

    async def text_json(self, system_prompt: str, user_prompt: str) -> dict:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = await self.chat_completion(messages, max_tokens=4096)
        return parse_json_response(raw)


def parse_json_response(raw: str | None) -> dict:
    if not raw or not raw.strip():
        raise RuntimeError("Empty AI response")

    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        raise RuntimeError("AI returned invalid JSON")
