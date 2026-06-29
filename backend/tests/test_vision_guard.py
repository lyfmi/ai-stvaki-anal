from app.schemas import AnalysisResult, VisionPayload
from app.services.ai.vision_guard import enforce_authoritative_teams, vision_needs_retry


def test_vision_needs_retry_when_france_but_notes_say_brazil_japan():
    vision = VisionPayload(
        home_team="France",
        away_team="Opponent",
        screenshot_notes="Brazil vs Japan World Cup match card",
        parse_confidence="high",
        odds_on_screenshot=True,
        available_outcomes=[{"label": "1", "coefficient": 1.74}],
    )
    assert vision_needs_retry(vision) is True


def test_enforce_scrubs_france_from_explanation():
    result = AnalysisResult(
        recommendation="П1 — Победа Франции",
        explanation="Франция является одним из фаворитов чемпионата.",
        arguments=["Франция сильная"],
        analysis_mode="pre_match",
        is_betting_recommendation=True,
    )
    out = enforce_authoritative_teams(result, "Brazil", "Japan", user_lang="ru")
    assert "франц" not in (out.recommendation or "").lower()
    assert "франц" not in (out.explanation or "").lower()
    assert "Brazil" in out.recommendation or "Бразил" in out.recommendation
