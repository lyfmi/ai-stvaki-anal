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
    ) -> tuple[str | None, str | None, str]:
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
        content = message.get("content")
        reasoning = message.get("reasoning")
        finish_reason = str(choice.get("finish_reason") or "stop")

        content_text = content.strip() if isinstance(content, str) and content.strip() else None
        reasoning_text = reasoning.strip() if isinstance(reasoning, str) and reasoning.strip() else None

        if not content_text and not reasoning_text:
            raise RuntimeError(f"Empty AI response (finish_reason={finish_reason})")

        if finish_reason == "length":
            logger.warning("AI response truncated at %s tokens", max_tokens)

        return content_text, reasoning_text, finish_reason

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
        raw_content, raw_reasoning, _ = await self.chat_completion(messages, max_tokens=8192)
        return parse_ai_json(raw_content, raw_reasoning)

    async def text_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 8192,
    ) -> dict:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw_content, raw_reasoning, finish_reason = await self.chat_completion(
            messages, max_tokens=max_tokens
        )
        data = parse_ai_json(raw_content, raw_reasoning)
        data["_finish_reason"] = finish_reason
        return data


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def _repair_malformed_json(text: str) -> str:
    repaired = text.strip()
    repaired = re.sub(
        r'^\{\s*",\s*"\s*:',
        '{"recommendation":',
        repaired,
    )
    repaired = re.sub(
        r'^\{\s*\\",\\"\s*:',
        '{"recommendation":',
        repaired,
    )
    return repaired


def _json_candidates(text: str) -> list[str]:
    cleaned = _strip_fences(text)
    candidates = [_repair_malformed_json(cleaned)]

    start = 0
    while True:
        start = cleaned.find("{", start)
        if start == -1:
            break
        depth = 0
        for index, char in enumerate(cleaned[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    fragment = cleaned[start : index + 1]
                    candidates.append(_repair_malformed_json(fragment))
                    candidates.append(fragment)
                    break
        start += 1

    candidates.append(cleaned)

    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            unique.append(candidate)
    return unique


def parse_json_response(raw: str | None) -> dict:
    if not raw or not raw.strip():
        raise RuntimeError("Empty AI response")

    for candidate in _json_candidates(raw):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        for candidate in (match.group(), _repair_malformed_json(match.group())):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise RuntimeError("AI returned invalid JSON")


def parse_ai_json(content: str | None, reasoning: str | None) -> dict:
    last_error: RuntimeError | None = None
    for source in (content, reasoning):
        if not source:
            continue
        try:
            return parse_json_response(source)
        except RuntimeError as exc:
            last_error = exc
    raise last_error or RuntimeError("AI returned invalid JSON")
