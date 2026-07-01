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


def test_rejects_group_placeholder_teams():
    kickoff = now_msk() + timedelta(hours=3)
    results = [
        SearchResultItem(
            query="q",
            title="World Cup 2026 | Match schedule, fixtures & stadiums - FIFA",
            snippet=(
                f"Match 79 – Group A winners v Group C/E/F/H/I third place - Mexico City Stadium. "
                f"Wednesday, {kickoff.strftime('%d %B %Y')}"
            ),
            url="https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtur",
        ),
        SearchResultItem(
            query="q",
            title="England v Congo DR: Line-ups, Score & Live Updates | Round of 32 - FIFA",
            snippet="England vs. Congo DR ; Competition. FIFA World Cup™ ; Kick Off. 1 July 2026, 16:00 ; Location. Atlanta Stadium",
            url="https://www.fifa.com/en/match-centre/match/17/285023/289287/400021512",
        ),
    ]
    picked = pick_fixture_from_search(results)
    assert picked is not None
    assert picked["home_team"] == "England"
    assert picked["away_team"] == "Congo DR"
    assert picked["kickoff_msk"].endswith("19:00 МСК")


def test_fifa_match_centre_kickoff_utc_to_msk():
    now = now_msk()
    kickoff = _parse_kickoff_from_text(
        "Kick Off. 1 July 2026, 16:00 ; Location. Atlanta Stadium",
        now,
        url="https://www.fifa.com/en/match-centre/match/17/285023/289287/400021512",
    )
    assert kickoff is not None
    assert kickoff.hour == 19
    assert kickoff.minute == 0
