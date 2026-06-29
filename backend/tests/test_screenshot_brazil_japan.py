"""Screenshot fixture tests — Brazil vs Japan (World Cup 2026) betting app capture."""
from __future__ import annotations

import json as json_module
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.schemas import SearchPayload, SearchResultItem, VisionPayload
from app.services.ai.pipeline import AiAnalysisPipeline, VisionExtractor
from app.services.ai.rag_search import build_rag_queries_for_vision

BRAZIL_JAPAN_VISION = {
    "sport": "football",
    "league": "FIFA World Cup 2026",
    "home_team": "Brazil",
    "away_team": "Japan",
    "match_datetime": "2026-06-29T20:00:00",
    "market_type": "1X2",
    "available_outcomes": [
        {"label": "1", "coefficient": 1.74},
        {"label": "X", "coefficient": 3.71},
        {"label": "2", "coefficient": 5.2},
    ],
    "screenshot_notes": "World Cup 2026 full-time result market visible",
    "search_queries": ["Brazil vs Japan World Cup 2026 lineups", "Brazil Japan head to head"],
    "parse_confidence": "high",
    "datetime_on_screenshot": True,
    "odds_on_screenshot": True,
    "match_status_hint": "upcoming",
}

BRAZIL_JAPAN_SYNTHESIS = {
    "recommendation": "П1 — Победа Brazil",
    "market": "1X2",
    "coefficient": 1.74,
    "probability_percent": 62,
    "risk": "medium",
    "arguments": ["Brazil сильнее по составу", "Japan редко побеждает топ-сборные"],
    "confidence": "medium",
    "explanation": "На скрине виден матч Brazil — Japan, коэффициент на П1 1.74.",
    "analysis_mode": "pre_match",
    "match_status_label": "Скоро",
    "match_datetime_msk": "29.06.2026 20:00 МСК",
    "is_betting_recommendation": True,
    "premium_insights": {
        "form_bars": [
            {"team": "Brazil", "wins": 4, "draws": 1, "losses": 0},
            {"team": "Japan", "wins": 2, "draws": 1, "losses": 2},
        ],
        "h2h": "Brazil чаще побеждает в очных встречах",
        "key_stats": [{"label": "xG/матч", "home": "1.9", "away": "1.1"}],
        "trends": ["Brazil не проигрывает в последних 5 матчах Кубка мира"],
        "advanced_arguments": ["Japan уступает по физике в единоборствах"],
    },
}


def _team_blob(vision: VisionPayload) -> str:
    return " ".join(
        filter(
            None,
            [vision.home_team, vision.away_team, vision.league, vision.screenshot_notes],
        )
    ).lower()


def test_screenshot_fixture_is_jpeg(screenshot_bytes):
    assert screenshot_bytes[:3] == b"\xff\xd8\xff"
    assert len(screenshot_bytes) > 50_000


def test_rag_queries_for_brazil_japan_vision():
    vision = VisionPayload.model_validate(BRAZIL_JAPAN_VISION)
    queries = build_rag_queries_for_vision(vision)
    assert len(queries) >= 4
    joined = " ".join(queries).lower()
    assert "brazil" in joined and "japan" in joined
    assert any("lineups" in q or "injuries" in q for q in queries)


@pytest.mark.asyncio
async def test_pipeline_e2e_mocked_groq_for_brazil_japan_screenshot(screenshot_bytes, monkeypatch):
    """Full pipeline: vision → RAG search → synthesis with mocked Groq HTTP."""

    async def fake_enrich(self, queries):
        return SearchPayload(
            queries_executed=queries[:2],
            results=[
                SearchResultItem(
                    query=queries[0],
                    title="Brazil vs Japan preview",
                    snippet="World Cup 2026 group stage preview and lineups",
                    url="https://example.com/preview",
                )
            ],
            search_status="ok",
        )

    monkeypatch.setattr(
        "app.services.ai.search_enricher.SearchEnricher.enrich",
        fake_enrich,
    )

    call_idx = {"n": 0}

    async def fake_post(url, *, headers=None, json=None, **kwargs):
        call_idx["n"] += 1
        messages = json["messages"]
        has_image = any(
            isinstance(m.get("content"), list)
            and any(p.get("type") == "image_url" for p in m["content"])
            for m in messages
            if m.get("role") == "user"
        )
        content = BRAZIL_JAPAN_VISION if has_image else BRAZIL_JAPAN_SYNTHESIS
        response = MagicMock()
        response.status_code = 200
        response.text = ""
        response.json.return_value = {
            "model": json["model"],
            "choices": [
                {
                    "message": {"content": json_module.dumps(content, ensure_ascii=False)},
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
        result = await AiAnalysisPipeline().analyze_screenshot(
            screenshot_bytes,
            "ru",
            filename="brazil_japan_screenshot.jpg",
            model="llama-3.3-70b-versatile",
        )

    vision = result["vision"]
    assert vision.parse_confidence != "failed"
    assert "brazil" in _team_blob(vision)
    assert "japan" in _team_blob(vision)
    assert vision.odds_on_screenshot is True

    analysis = result["result"]
    assert analysis.recommendation
    assert analysis.coefficient == 1.74
    assert result["pipeline_version"] == settings.ai_pipeline_version
    assert result["latency_ms"]["total"] >= 0
    assert call_idx["n"] >= 2


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.groq_api_key, reason="GROQ_API_KEY not configured")
async def test_live_groq_vision_reads_brazil_japan_from_screenshot(screenshot_bytes):
    """Live Groq vision on user-provided screenshot — proof of multimodal parsing."""
    vision = await VisionExtractor().extract(
        screenshot_bytes,
        filename="brazil_japan_screenshot.jpg",
        model="meta-llama/llama-4-scout-17b-16e-instruct",
    )

    blob = _team_blob(vision)
    assert vision.parse_confidence != "failed", vision.model_dump()
    assert "brazil" in blob, vision.model_dump()
    assert "japan" in blob, vision.model_dump()
    assert vision.odds_on_screenshot is True
    coeffs = [o.coefficient for o in vision.available_outcomes if o.coefficient]
    if coeffs:
        assert any(1.5 <= c <= 2.0 for c in coeffs), coeffs


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.groq_api_key, reason="GROQ_API_KEY not configured")
async def test_live_groq_text_model_returns_json(screenshot_bytes):
    """Smoke test: default text model answers with valid JSON (max_tokens=1024)."""
    from app.services.ai.providers.groq_client import GroqClient

    client = GroqClient()
    data = await client.text_json(
        "Return JSON only.",
        'Return {"status":"ok","teams":["Brazil","Japan"]}',
        model="llama-3.3-70b-versatile",
    )
    assert data.get("status") == "ok"
    teams = [t.lower() for t in (data.get("teams") or [])]
    assert "brazil" in teams and "japan" in teams
