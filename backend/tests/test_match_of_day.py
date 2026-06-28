"""Tests for match of day cache key and fallback."""
from app.services.ai.match_context import msk_date_key
from app.services.match_of_day import CACHE_PREFIX, FALLBACK_MATCH


def test_cache_key_uses_msk_date():
    key = f"{CACHE_PREFIX}:{msk_date_key()}"
    assert key.startswith("match_of_day:v1:")
    assert len(key.split(":")[-1]) == 10


def test_fallback_match_has_required_fields():
    assert "home_team" in FALLBACK_MATCH
    assert "away_team" in FALLBACK_MATCH
    assert "league" in FALLBACK_MATCH
    assert "kickoff_msk" in FALLBACK_MATCH
    assert "teaser" in FALLBACK_MATCH
