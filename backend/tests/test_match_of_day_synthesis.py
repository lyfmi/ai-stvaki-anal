"""Tests for match-of-day synthesis (including live mode)."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest

from app.schemas import SearchPayload, SearchResultItem, VisionPayload
from app.services.ai.match_context import now_msk, resolve_match_context
from app.services.ai.pipeline import Synthesizer

LIVE_SYNTHESIS = {
    "recommendation": "П1 — Победа Brazil",
    "market": "1X2",
    "coefficient": None,
    "probability_percent": None,
    "risk": "medium",
    "arguments": ["Brazil контролирует игру"],
    "confidence": "medium",
    "explanation": "Brazil сильнее в текущем матче против Japan.",
    "analysis_mode": "live",
    "match_status_label": "Идёт сейчас",
    "match_datetime_msk": "29.06.2026 20:00 МСК",
    "is_betting_recommendation": True,
    "premium_insights": {
        "form_bars": [
            {"team": "Brazil", "wins": 3, "draws": 1, "losses": 1},
            {"team": "Japan", "wins": 2, "draws": 1, "losses": 2},
        ],
        "h2h": "Brazil чаще побеждает",
        "key_stats": [{"label": "Голы/матч", "home": "1.8", "away": "1.1"}],
        "trends": ["Brazil атакует активнее"],
        "advanced_arguments": [],
    },
    "final_score": None,
    "winner": None,
    "_finish_reason": "stop",
}


@pytest.mark.asyncio
async def test_synthesize_match_of_day_live_returns_recommendation():
    kickoff = now_msk() - timedelta(minutes=30)
    match = {
        "home_team": "Brazil",
        "away_team": "Japan",
        "league": "FIFA World Cup 2026",
        "kickoff_msk": kickoff.strftime("%d.%m.%Y %H:%M МСК"),
        "kickoff_at": kickoff.isoformat(),
        "is_live": True,
    }
    search = SearchPayload(
        results=[
            SearchResultItem(
                query="q",
                title="Brazil vs Japan live",
                snippet="World Cup 2026 live from Houston",
                url="https://example.com",
            )
        ],
        search_status="ok",
    )

    synthesizer = Synthesizer()
    synthesizer.client.text_json = AsyncMock(return_value=dict(LIVE_SYNTHESIS))

    result = await synthesizer.synthesize_match_of_day(match, search, "ru")

    assert result.recommendation
    assert "Бразилия" in result.recommendation
    assert result.analysis_mode == "live"
    synthesizer.client.text_json.assert_awaited()


def test_resolve_match_context_keeps_upcoming_when_search_says_live():
    vision = VisionPayload(
        home_team="Brazil",
        away_team="Japan",
        match_status_hint="upcoming",
        datetime_on_screenshot=False,
    )
    search = SearchPayload(
        results=[
            SearchResultItem(
                query="q",
                title="Brazil vs Japan live stream",
                snippet="Watch Brazil Japan live now",
                url="https://example.com",
            )
        ]
    )
    ctx = resolve_match_context(vision, search, user_lang="ru")
    assert ctx.analysis_mode == "pre_match"
