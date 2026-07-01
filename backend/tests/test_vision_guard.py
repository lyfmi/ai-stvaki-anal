from app.schemas import AnalysisResult, SearchPayload, SearchResultItem, VisionPayload
from app.services.ai.vision_guard import (
    enforce_authoritative_teams,
    filter_search_for_teams,
    is_placeholder_team,
    vision_needs_retry,
    vision_teams_valid,
)


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


def test_enforce_dedupes_identical_scrubbed_arguments():
    result = AnalysisResult(
        recommendation="П1 — Победа Brazil",
        arguments=[
            "Франция доминирует в классике",
            "Франция сильнее в атаке",
            "Франция лучше по составу",
        ],
        analysis_mode="pre_match",
        is_betting_recommendation=True,
    )
    out = enforce_authoritative_teams(result, "Brazil", "Japan", user_lang="ru")
    assert len(out.arguments) >= 1
    assert len(out.arguments) <= 3
    assert len({a.casefold() for a in out.arguments}) == len(out.arguments)


def test_vision_needs_retry_for_placeholder_teams():
    vision = VisionPayload(
        home_team="Домашняя",
        away_team="Гостевая",
        parse_confidence="high",
        odds_on_screenshot=True,
        available_outcomes=[{"label": "1", "coefficient": 1.74}],
    )
    assert vision_needs_retry(vision) is True
    assert vision_teams_valid(vision) is False
    assert is_placeholder_team("Home") is True
    assert is_placeholder_team("Brazil") is False


def test_filter_search_keeps_original_when_no_team_match():
    search = SearchPayload(
        queries_executed=["q"],
        results=[
            SearchResultItem(
                query="q",
                title="Unrelated headline",
                snippet="Some other match preview",
                url="https://example.com",
            )
        ],
        search_status="ok",
    )
    filtered = filter_search_for_teams(search, "Brazil", "Japan")
    assert len(filtered.results) == 1
    assert filtered.results[0].title == "Unrelated headline"
