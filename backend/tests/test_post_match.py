from app.schemas import AnalysisResult, VisionPayload
from app.services.ai.match_context import MatchContextOut, resolve_match_context
from app.services.ai.normalize import apply_post_match_overrides
from app.services.ai.rag_search import build_rag_queries_for_fixture


def test_resolve_post_match_when_final_score_on_vision():
    """Finished match on screenshot wins over future kickoff datetime."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    MSK = ZoneInfo("Europe/Moscow")
    future = datetime.now(MSK) + timedelta(days=1)
    vision = VisionPayload(
        home_team="Brazil",
        away_team="Japan",
        match_datetime=future.isoformat(),
        match_status_hint="finished",
        final_score="2:1",
        winner="Brazil",
        datetime_on_screenshot=True,
    )
    from app.schemas import SearchPayload

    ctx = resolve_match_context(vision, SearchPayload(), user_lang="ru")
    assert ctx.analysis_mode == "post_match"


def test_apply_post_match_overrides_clears_betting_fields():
    result = AnalysisResult(
        recommendation="Brazil 2:1 Japan",
        coefficient=1.74,
        probability_percent=65,
        analysis_mode="post_match",
        is_betting_recommendation=True,
    )
    ctx = MatchContextOut(analysis_mode="post_match", match_status_label="Матч завершён")
    vision = VisionPayload(final_score="2:1", winner="Brazil")
    out = apply_post_match_overrides(result, vision=vision, ctx=ctx)
    assert out.is_betting_recommendation is False
    assert out.coefficient is None
    assert out.probability_percent is None
    assert out.final_score == "2:1"
    assert out.winner == "Brazil"


def test_fixture_rag_queries_prioritize_1win_odds():
    queries = build_rag_queries_for_fixture(
        {"home_team": "Brazil", "away_team": "Japan", "league": "World Cup"}
    )
    assert any("1win" in q.lower() for q in queries)
    assert queries[0].lower().startswith("brazil vs japan")
