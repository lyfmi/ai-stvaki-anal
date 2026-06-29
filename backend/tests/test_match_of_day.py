"""Tests for match of day cache key and search parser."""
from datetime import timedelta

from app.schemas import SearchResultItem
from app.services.ai.match_context import msk_date_key, now_msk
from app.services.match_of_day import CACHE_PREFIX, MatchOfDayService
from app.services.match_of_day_parser import pick_fixture_from_search


def test_cache_key_uses_msk_date():
    key = f"{CACHE_PREFIX}:{msk_date_key()}"
    assert key.startswith("match_of_day:v2:")
    assert len(key.split(":")[-1]) == 10


def test_pick_fixture_from_fifa_snippet():
    results = [
        SearchResultItem(
            query="q",
            title="South Africa v Canada | World Cup Round of 32 | Match Preview - FIFA",
            snippet="Sunday, 28 June | Los Angeles Stadium. Kick-off time 21:00 SAST",
            url="https://fifa.com",
        ),
        SearchResultItem(
            query="q",
            title="Brazil v Japan | FIFA World Cup Round of 32",
            snippet="Monday 29 June 2026 Houston Stadium GMT 17:00",
            url="https://fifa.com",
        ),
    ]
    picked = pick_fixture_from_search(results)
    assert picked is not None
    assert picked["home_team"] == "Brazil"
    assert picked["away_team"] == "Japan"


def test_espn_live_score_archive_not_picked():
    results = [
        SearchResultItem(
            query="q",
            title="South Africa vs. Canada (Jun 28, 2026) Live Score - ESPN",
            snippet="Final score and match highlights",
            url="https://espn.com",
        ),
        SearchResultItem(
            query="q",
            title="Brazil v Japan | FIFA World Cup Round of 32",
            snippet="Monday 29 June 2026 Houston Stadium GMT 17:00",
            url="https://fifa.com",
        ),
    ]
    picked = pick_fixture_from_search(results)
    assert picked is not None
    assert picked["home_team"] == "Brazil"
    assert picked["away_team"] == "Japan"
    assert picked["is_live"] is False


def test_normalize_allows_live_match():
    svc = MatchOfDayService()
    kickoff = now_msk() - timedelta(minutes=45)
    raw = {
        "home_team": "South Africa",
        "away_team": "Canada",
        "league": "World Cup",
        "kickoff_msk": kickoff.strftime("%d.%m.%Y %H:%M МСК"),
        "kickoff_at": kickoff.isoformat(),
        "teaser": "Live",
    }
    normalized = svc._normalize_match(raw)
    assert normalized is not None
    assert normalized["is_live"] is True


def test_normalize_allows_tomorrow_match():
    svc = MatchOfDayService()
    kickoff = now_msk() + timedelta(hours=20)
    raw = {
        "home_team": "Brazil",
        "away_team": "Japan",
        "league": "World Cup",
        "kickoff_msk": kickoff.strftime("%d.%m.%Y %H:%M МСК"),
        "kickoff_at": kickoff.isoformat(),
        "teaser": "Soon",
    }
    normalized = svc._normalize_match(raw)
    assert normalized is not None
    assert normalized["is_live"] is False
