from app.schemas import AnalysisResult, SearchPayload, VisionPayload
from app.services.ai.pipeline import Synthesizer
from app.services.ai.odds_resolver import ensure_fixture_premium_insights


def test_ensure_premium_insights_backfills_charts():
    result = AnalysisResult(
        recommendation="П1 — Победа Brazil",
        analysis_mode="pre_match",
        is_betting_recommendation=True,
    )
    out = ensure_fixture_premium_insights(result, "Brazil", "Japan")
    assert out.premium_insights is not None
    assert len(out.premium_insights.form_bars) == 2
    assert len(out.premium_insights.key_stats) >= 1


def test_dedupe_arguments_in_normalize():
    from app.services.ai.normalize import normalize_analysis_data

    data = {
        "recommendation": "П1 — Победа Brazil",
        "market": "1X2",
        "arguments": ["Same point", "Same point", "Unique point"],
        "confidence": "medium",
        "risk": "low",
        "explanation": "Test",
        "analysis_mode": "pre_match",
        "match_status_label": "Скоро",
        "is_betting_recommendation": True,
    }
    normalized = normalize_analysis_data(data)
    assert normalized["arguments"] == ["Same point", "Unique point"]
