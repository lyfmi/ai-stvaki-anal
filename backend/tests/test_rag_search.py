from app.services.ai.rag_search import build_rag_match_queries, build_rag_queries_for_fixture


def test_build_rag_match_queries():
    queries = build_rag_match_queries("Brazil", "Japan", league="World Cup")
    assert len(queries) == 4
    assert any("lineups" in q for q in queries)
    assert any("injuries" in q for q in queries)


def test_build_rag_queries_for_fixture():
    queries = build_rag_queries_for_fixture(
        {"home_team": "Brazil", "away_team": "Japan", "league": "World Cup 2026"}
    )
    assert len(queries) >= 4
    assert any("Brazil vs Japan" in q for q in queries)
