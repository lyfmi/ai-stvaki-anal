import json as json_module
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.services.ai.providers.groq_client import GroqClient, _inject_images


def test_inject_images_attaches_base64_to_last_user_message(screenshot_bytes):
    messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "analyze screenshot"},
    ]
    out = _inject_images(messages, [screenshot_bytes], "image/jpeg")
    user = out[-1]
    assert user["role"] == "user"
    assert isinstance(user["content"], list)
    assert user["content"][0] == {"type": "text", "text": "analyze screenshot"}
    image_part = user["content"][1]
    assert image_part["type"] == "image_url"
    assert image_part["image_url"]["url"].startswith("data:image/jpeg;base64,")


@pytest.mark.asyncio
async def test_chat_completion_posts_groq_openai_payload(screenshot_bytes):
    captured: dict = {}

    async def fake_post(url, *, headers=None, json=None, **kwargs):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        response = MagicMock()
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
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            images=[screenshot_bytes],
        )

    assert captured["url"] == f"{settings.groq_api_base.rstrip('/')}/chat/completions"
    assert captured["headers"]["Authorization"].startswith("Bearer ")
    payload = captured["json"]
    assert payload["model"] == "meta-llama/llama-4-scout-17b-16e-instruct"
    assert payload["max_tokens"] == settings.groq_max_tokens == 1024
    assert payload["response_format"] == {"type": "json_object"}
    parts = payload["messages"][-1]["content"]
    assert any(part.get("type") == "image_url" for part in parts)
    assert content is not None
    assert model_used == "meta-llama/llama-4-scout-17b-16e-instruct"
    assert finish == "stop"
