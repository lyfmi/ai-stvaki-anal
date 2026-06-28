"""Tests for match context MSK logic and smart search queries."""
from datetime import datetime, timedelta, timezone

from app.schemas import SearchPayload, SearchResultItem, VisionPayload
from app.services.ai.match_context import (
    build_smart_search_queries,
    format_datetime_msk,
    msk_date_key,
    resolve_match_context,
)
from zoneinfo import ZoneInfo

MSK = ZoneInfo("Europe/Moscow")


def test_msk_date_key_format():
    key = msk_date_key()
    assert len(key) == 10
    assert key[4] == "-"


def test_build_smart_search_queries_missing_odds_and_time():
    vision = VisionPayload(
        home_team="Arsenal",
        away_team="Chelsea",
        datetime_on_screenshot=False,
        odds_on_screenshot=False,
        match_status_hint="unknown",
        search_queries=["Arsenal Chelsea preview"],
    )
    queries = build_smart_search_queries(vision)
    assert any("kickoff" in q.lower() for q in queries)
    assert any("odds" in q.lower() for q in queries)
    assert any("result" in q.lower() for q in queries)
    assert "Arsenal Chelsea preview" in queries


def test_resolve_post_match_from_hint():
    vision = VisionPayload(
        home_team="A",
        away_team="B",
        match_status_hint="finished",
        datetime_on_screenshot=True,
    )
    search = SearchPayload()
    ctx = resolve_match_context(vision, search, user_lang="ru")
    assert ctx.analysis_mode == "post_match"
    assert ctx.match_status_label == "Матч завершён"


def test_resolve_pre_match_future_kickoff():
    future = datetime.now(MSK) + timedelta(days=2)
    vision = VisionPayload(
        home_team="A",
        away_team="B",
        match_datetime=future.isoformat(),
        datetime_on_screenshot=True,
        match_status_hint="upcoming",
    )
    search = SearchPayload()
    ctx = resolve_match_context(vision, search, user_lang="ru")
    assert ctx.analysis_mode == "pre_match"
    assert ctx.match_datetime_msk == format_datetime_msk(future)


def test_resolve_post_match_past_kickoff():
    past = datetime.now(MSK) - timedelta(days=1)
    vision = VisionPayload(
        home_team="A",
        away_team="B",
        match_datetime=past.astimezone(timezone.utc).isoformat(),
        datetime_on_screenshot=True,
        match_status_hint="upcoming",
    )
    search = SearchPayload()
    ctx = resolve_match_context(vision, search, user_lang="ru")
    assert ctx.analysis_mode == "post_match"


def test_search_indicates_finished():
    vision = VisionPayload(home_team="A", away_team="B", match_status_hint="unknown")
    search = SearchPayload(
        results=[
            SearchResultItem(
                query="q",
                title="Full time",
                snippet="Final score 2-1",
                url="",
            )
        ]
    )
    ctx = resolve_match_context(vision, search, user_lang="en")
    assert ctx.analysis_mode == "post_match"
    assert ctx.match_status_label == "Match finished"
