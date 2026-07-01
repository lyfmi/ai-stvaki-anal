"""RAG-style web search query builders for lineups, injuries, and match context."""
from __future__ import annotations

from app.schemas import VisionPayload


def build_rag_match_queries(home: str, away: str, *, league: str | None = None) -> list[str]:
    home = home.strip()
    away = away.strip()
    if not home or not away:
        return []
    pair = f"{home} vs {away}"
    league_bit = f" {league}" if league else ""
    return [
        f"{pair}{league_bit} predicted lineups starting XI",
        f"{pair} team news injuries suspensions",
        f"{pair} head to head recent form stats",
        f"{pair} прогноз составы травмы статистика",
    ]


def merge_search_queries(*groups: list[str], limit: int = 6) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for query in group:
            key = query.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(query.strip())
            if len(merged) >= limit:
                return merged
    return merged


def build_rag_queries_for_vision(vision: VisionPayload) -> list[str]:
    from app.services.ai.match_context import build_smart_search_queries

    home = (vision.home_team or "").strip()
    away = (vision.away_team or "").strip()
    base = build_smart_search_queries(vision)
    rag = build_rag_match_queries(home, away, league=vision.league)
    return merge_search_queries(base, rag, limit=6)


def build_rag_queries_for_fixture(match: dict) -> list[str]:
    home = str(match.get("home_team", "")).strip()
    away = str(match.get("away_team", "")).strip()
    league = str(match.get("league", "")).strip() or None
    pair = f"{home} vs {away}"
    odds = [
        f"{pair} odds 1x2 betting",
        f"{pair} 1win betting odds coefficient",
        f"{pair} коэффициенты букмекер прогноз",
    ]
    base = [
        f"{pair} preview prediction",
        f"{pair} betting analysis",
    ]
    rag = build_rag_match_queries(home, away, league=league)
    return merge_search_queries(odds, base, rag, limit=6)
