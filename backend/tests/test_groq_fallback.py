import json as json_module
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.services.ai.providers.groq_client import GroqClient
from app.services.ai.providers.groq_errors import GroqApiError


@pytest.mark.asyncio
async def test_chat_completion_falls_back_on_rate_limit():
    calls: list[str] = []

    async def fake_post(url, *, headers=None, json=None, **kwargs):
        calls.append(json["model"])
        response = MagicMock()
        if json["model"] == "llama-3.3-70b-versatile":
            response.status_code = 429
            response.text = '{"error":{"message":"rate_limit_exceeded","type":"tokens"}}'
            return response
        response.status_code = 200
        response.text = ""
        response.json.return_value = {
            "model": json["model"],
            "choices": [
                {
                    "message": {"content": json_module.dumps({"ok": True})},
                    "finish_reason": "stop",
                }
            ],
        }
        return response

    client = AsyncMock()
    client.post = fake_post
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None

    with patch("app.services.ai.providers.groq_client.httpx.AsyncClient", return_value=client):
        groq = GroqClient()
        content, model_used, finish = await groq.chat_completion(
            [{"role": "user", "content": "parse"}],
            model="llama-3.3-70b-versatile",
        )

    assert calls[0] == "llama-3.3-70b-versatile"
    assert model_used == "qwen/qwen3-32b"
    assert content is not None
    assert finish == "stop"


@pytest.mark.asyncio
async def test_chat_completion_raises_when_all_models_rate_limited():
    async def fake_post(url, *, headers=None, json=None, **kwargs):
        response = MagicMock()
        response.status_code = 429
        response.text = '{"error":{"message":"rate_limit_exceeded"}}'
        return response

    client = AsyncMock()
    client.post = fake_post
    client.__aenter__.return_value = client
    client.__aexit__.return_value = None

    with patch("app.services.ai.providers.groq_client.httpx.AsyncClient", return_value=client):
        groq = GroqClient()
        with pytest.raises(GroqApiError) as exc:
            await groq.chat_completion([{"role": "user", "content": "parse"}])
    assert exc.value.is_rate_limit
