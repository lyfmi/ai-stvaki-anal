"""Tests for smart search query builder."""
from app.schemas import VisionPayload
from app.services.ai.match_context import build_smart_search_queries


def test_dedupes_queries():
    vision = VisionPayload(
        home_team="Real",
        away_team="Barca",
        datetime_on_screenshot=False,
        odds_on_screenshot=False,
        match_status_hint="upcoming",
        search_queries=["real vs barca odds"],
    )
    queries = build_smart_search_queries(vision)
    lower = [q.lower() for q in queries]
    assert len(lower) == len(set(lower))


def test_no_auto_queries_without_teams():
    vision = VisionPayload(
        datetime_on_screenshot=False,
        odds_on_screenshot=False,
        search_queries=["football today"],
    )
    queries = build_smart_search_queries(vision)
    assert queries == ["football today"]
