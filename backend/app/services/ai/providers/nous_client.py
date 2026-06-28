import base64
import json
import re
from typing import Any

import httpx

from app.core.config import settings


class NousClient:
    def __init__(self) -> None:
        self.base_url = settings.nous_api_base.rstrip("/")
        self.api_key = settings.nous_api_key
        self.model = settings.nous_model

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> str:
        if not self.api_key:
            raise RuntimeError("NOUS_API_KEY is not configured")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def vision_json(self, image_bytes: bytes, system_prompt: str, user_prompt: str) -> dict:
        b64 = base64.b64encode(image_bytes).decode()
        content = [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        ]
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]
        raw = await self.chat_completion(messages)
        return parse_json_response(raw)

    async def text_json(self, system_prompt: str, user_prompt: str) -> dict:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = await self.chat_completion(messages)
        return parse_json_response(raw)


def parse_json_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise
