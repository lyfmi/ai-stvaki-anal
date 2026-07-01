"""Tests for GMT-before-time kickoff parsing in match of day parser."""
from datetime import timedelta

from app.schemas import SearchResultItem
from app.services.ai.match_context import now_msk
from app.services.match_of_day_parser import (
    _fallback_kickoff_from_date,
    _parse_kickoff_from_text,
    pick_fixture_from_search,
)


def test_parse_gmt_before_time():
    now = now_msk()
    kickoff = _parse_kickoff_from_text(
        "Monday 29 June 2026 Houston Stadium GMT 17:00",
        now,
    )
    assert kickoff is not None
    assert kickoff.hour == 20
    assert kickoff.minute == 0


def test_fallback_kickoff_from_fifa_snippet_without_time():
    now = now_msk()
    kickoff_day = now + timedelta(days=1)
    blob = kickoff_day.strftime("Brazil v Japan | FIFA World Cup 2026 | %A, %d %B %Y")
    kickoff = _fallback_kickoff_from_date(blob, blob, now)
    assert kickoff is not None
    assert kickoff.day == kickoff_day.day
    assert kickoff.month == kickoff_day.month


def test_pick_fixture_em_dash_teams():
    kickoff = now_msk() + timedelta(hours=20)
    results = [
        SearchResultItem(
            query="q",
            title="Brazil — Japan | FIFA World Cup 2026",
            snippet=kickoff.strftime("Monday, %d %B %Y | Houston Stadium GMT 17:00"),
            url="https://www.fifa.com/en/tournaments/mens/worldcup",
        )
    ]
    picked = pick_fixture_from_search(results)
    assert picked is not None
    assert picked["home_team"] == "Brazil"
    assert picked["away_team"] == "Japan"
