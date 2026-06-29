"""Tests for GMT-before-time kickoff parsing in match of day parser."""
from app.services.ai.match_context import now_msk
from app.services.match_of_day_parser import _parse_kickoff_from_text


def test_parse_gmt_before_time():
    now = now_msk()
    kickoff = _parse_kickoff_from_text(
        "Monday 29 June 2026 Houston Stadium GMT 17:00",
        now,
    )
    assert kickoff is not None
    assert kickoff.hour == 20
    assert kickoff.minute == 0
