"""Tests for AI response normalization edge cases."""
from app.services.ai.normalize import parse_analysis_result
from app.services.team_names import localize_match_dict, localize_team_name


def test_parse_analysis_result_accepts_false_premium_insights():
    data = {
        "recommendation": "П1 — Победа Англия",
        "market": "1X2",
        "coefficient": None,
        "probability_percent": None,
        "risk": "medium",
        "arguments": ["Англия сильнее"],
        "confidence": "medium",
        "explanation": "Англия фаворит.",
        "analysis_mode": "pre_match",
        "match_status_label": "Скоро",
        "is_betting_recommendation": True,
        "premium_insights": False,
    }
    result = parse_analysis_result(data)
    assert result.recommendation.startswith("П1")
    assert result.premium_insights is None


def test_localize_team_names_ru():
    assert localize_team_name("England", "ru") == "Англия"
    assert localize_team_name("Congo DR", "ru") == "ДР Конго"
    localized = localize_match_dict(
        {
            "home_team": "England",
            "away_team": "Congo DR",
            "league": "FIFA World Cup 2026",
        },
        "ru",
    )
    assert localized["home_team"] == "Англия"
    assert localized["away_team"] == "ДР Конго"
    assert localized["league"] == "ЧМ-2026"
