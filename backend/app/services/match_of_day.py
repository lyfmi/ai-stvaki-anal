"""Daily featured match selection via web search + AI."""
from __future__ import annotations

import json
import logging

from pydantic import ValidationError

from app.core.config import settings
from app.core.redis import get_redis
from app.schemas import MatchOfDayOut
from app.services.ai.match_context import msk_date_key
from app.services.ai.providers.nous_client import NousClient
from app.services.ai.search_enricher import SearchEnricher

logger = logging.getLogger(__name__)

CACHE_PREFIX = "match_of_day:v1"
CACHE_TTL = 86400

FALLBACK_MATCH = {
    "home_team": "Real Madrid",
    "away_team": "Barcelona",
    "league": "La Liga",
    "kickoff_msk": "21:00 МСК",
    "teaser": "El Clásico — один из главных матчей сезона",
}

PICK_SYSTEM = """You pick one interesting football match happening today or tonight (MSK timezone).
Return JSON only with keys: home_team, away_team, league, kickoff_msk, teaser.
kickoff_msk format: "HH:MM МСК" or "DD.MM.YYYY HH:MM МСК".
teaser: one short sentence in Russian why this match is interesting."""

PICK_USER_TEMPLATE = """Today's date MSK: {date_msk}

Search snippets about today's football fixtures:
{search_json}

Pick ONE top match from European leagues (Premier League, La Liga, Serie A, Bundesliga, UCL).
Prefer high-profile fixtures. Return JSON only."""


class MatchOfDayService:
    def __init__(self) -> None:
        self.search = SearchEnricher()
        self.client = NousClient()

    def _cache_key(self) -> str:
        return f"{CACHE_PREFIX}:{msk_date_key()}"

    async def get_match(self) -> MatchOfDayOut:
        redis = await get_redis()
        key = self._cache_key()
        cached = await redis.get(key)
        if cached:
            data = json.loads(cached)
            return MatchOfDayOut(**data, cached=True)

        match = await self._fetch_and_pick()
        await redis.setex(key, CACHE_TTL, json.dumps(match))
        return MatchOfDayOut(**match, cached=False)

    async def _fetch_and_pick(self) -> dict:
        if settings.ai_mock:
            return dict(FALLBACK_MATCH)

        queries = [
            "football fixtures today Champions League Premier League La Liga",
            "best football matches today",
        ]
        payload = await self.search.enrich(queries)
        if payload.search_status == "failed" or not payload.results:
            logger.warning("Match of day search failed, using fallback")
            return dict(FALLBACK_MATCH)

        search_json = json.dumps(
            [{"title": r.title, "snippet": r.snippet} for r in payload.results[:8]],
            ensure_ascii=False,
        )
        user_prompt = PICK_USER_TEMPLATE.format(date_msk=msk_date_key(), search_json=search_json)
        try:
            data = await self.client.text_json(PICK_SYSTEM, user_prompt)
            match = {
                "home_team": str(data.get("home_team", FALLBACK_MATCH["home_team"])),
                "away_team": str(data.get("away_team", FALLBACK_MATCH["away_team"])),
                "league": str(data.get("league", FALLBACK_MATCH["league"])),
                "kickoff_msk": str(data.get("kickoff_msk", FALLBACK_MATCH["kickoff_msk"])),
                "teaser": str(data.get("teaser", FALLBACK_MATCH["teaser"])),
            }
            return match
        except (ValidationError, RuntimeError, KeyError) as exc:
            logger.warning("Match of day AI pick failed: %s", exc)
            return dict(FALLBACK_MATCH)
