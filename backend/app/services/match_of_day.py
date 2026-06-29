"""Daily featured match selection via web search + AI (cached, refreshed every 15 min)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from pydantic import ValidationError

from app.core.config import settings
from app.core.redis import get_redis
from app.schemas import MatchOfDayOut
from app.services.ai.match_context import (
    format_datetime_msk,
    is_kickoff_expired,
    msk_date_key,
    now_msk,
    parse_kickoff_msk,
)
from app.services.ai.providers.groq_client import GroqClient
from app.services.ai.providers.json_utils import parse_ai_json
from app.services.ai.search_enricher import SearchEnricher
from app.services.match_of_day_parser import pick_fixture_from_search

logger = logging.getLogger(__name__)

CACHE_PREFIX = "match_of_day:v2"
CACHE_TTL = 900  # 15 minutes — users read cache only
REFRESH_LOCK_KEY = "match_of_day:refresh_lock"
REFRESH_LOCK_TTL = 120
EMPTY_CACHE_TTL = 300

PICK_SYSTEM = """You pick ONE real football match from search snippets for the match-of-day card.
Return ONLY valid JSON with keys: home_team, away_team, league, kickoff_msk, kickoff_at, teaser.
Priority order:
1) LIVE match right now (already kicked off, not finished)
2) Upcoming match today MSK
3) Upcoming match tomorrow MSK
Do NOT invent fixtures — only use teams explicitly mentioned in search snippets.
kickoff_msk: "DD.MM.YYYY HH:MM МСК"
kickoff_at: ISO 8601 with +03:00 timezone
teaser: one short Russian sentence why this match matters"""

PICK_USER_TEMPLATE = """Current MSK datetime: {now_msk}
Today's date MSK: {date_msk}

Pick the best match for users RIGHT NOW. Prefer LIVE if any match already started.
If South Africa vs Canada or Brazil vs Japan appear — use real kickoff from snippets.

Search snippets:
{search_json}

Return JSON only."""

PICK_REPAIR = """Return ONLY one JSON object with keys:
home_team, away_team, league, kickoff_msk, kickoff_at, teaser.
No markdown, no extra text."""

EMPTY_MATCH = MatchOfDayOut(
    home_team="—",
    away_team="—",
    league="Football",
    kickoff_msk="Скоро",
    kickoff_at=None,
    teaser="Сейчас нет актуального матча — загрузите скрин события.",
    cached=False,
    is_live=False,
)


class MatchOfDayService:
    def __init__(self) -> None:
        self.search = SearchEnricher()
        self.client = GroqClient()

    def _cache_key(self) -> str:
        return f"{CACHE_PREFIX}:{msk_date_key()}"

    def _is_relevant_kickoff(self, kickoff_dt: datetime) -> bool:
        now = now_msk()
        if is_kickoff_expired(kickoff_dt, live_buffer_minutes=105):
            return False
        if kickoff_dt <= now < kickoff_dt + timedelta(minutes=130):
            return True
        if kickoff_dt > now and kickoff_dt <= now + timedelta(hours=36):
            return True
        return False

    def _normalize_match(self, raw: dict) -> dict | None:
        kickoff_at_str = raw.get("kickoff_at")
        kickoff_msk = str(raw.get("kickoff_msk", "")).strip()
        kickoff_dt: datetime | None = None

        if kickoff_at_str:
            try:
                kickoff_dt = datetime.fromisoformat(str(kickoff_at_str).replace("Z", "+00:00"))
                if kickoff_dt.tzinfo is None:
                    from zoneinfo import ZoneInfo

                    kickoff_dt = kickoff_dt.replace(tzinfo=ZoneInfo("Europe/Moscow"))
            except ValueError:
                kickoff_dt = None

        if kickoff_dt is None and kickoff_msk:
            kickoff_dt = parse_kickoff_msk(kickoff_msk)

        if kickoff_dt is None or not self._is_relevant_kickoff(kickoff_dt):
            return None

        home = str(raw.get("home_team", "")).strip()
        away = str(raw.get("away_team", "")).strip()
        junk = ("news", "times", "breaking", "youtube", "wikipedia")
        if not home or not away or any(w in home.lower() for w in junk) or any(w in away.lower() for w in junk):
            return None

        now = now_msk()
        is_live = kickoff_dt <= now < kickoff_dt + timedelta(minutes=130)

        return {
            "home_team": str(raw.get("home_team", "")).strip() or "Team A",
            "away_team": str(raw.get("away_team", "")).strip() or "Team B",
            "league": str(raw.get("league", "Football")).strip(),
            "kickoff_msk": format_datetime_msk(kickoff_dt),
            "kickoff_at": kickoff_dt.isoformat(),
            "teaser": str(raw.get("teaser", "Интересный матч")).strip(),
            "is_live": is_live,
        }

    async def _pick_with_ai(self, search_json: str, now: datetime) -> dict | None:
        user_prompt = PICK_USER_TEMPLATE.format(
            now_msk=format_datetime_msk(now),
            date_msk=msk_date_key(),
            search_json=search_json,
        )
        try:
            content, _, _ = await self.client.chat_completion(
                [
                    {"role": "system", "content": PICK_SYSTEM},
                    {"role": "user", "content": user_prompt},
                ],
            )
            data = parse_ai_json(content)
            normalized = self._normalize_match(data)
            if normalized:
                return normalized
        except Exception as exc:
            logger.warning("Match of day AI pick failed: %s", exc)

        try:
            repair_prompt = f"{user_prompt}\n\nInvalid or missing fields. {PICK_REPAIR}"
            content, _, _ = await self.client.chat_completion(
                [
                    {"role": "system", "content": PICK_SYSTEM},
                    {"role": "user", "content": repair_prompt},
                ],
            )
            data = parse_ai_json(content)
            return self._normalize_match(data)
        except Exception as exc:
            logger.warning("Match of day AI repair failed: %s", exc)
            return None

    def _build_queries(self, now: datetime) -> list[str]:
        date_human = now.strftime("%d %B %Y")
        tomorrow = (now + timedelta(days=1)).strftime("%d %B %Y")
        return [
            "South Africa v Canada FIFA World Cup 2026 kickoff June 28 live",
            "Brazil v Japan FIFA World Cup 2026 June 29 kickoff Houston",
            f"FIFA World Cup 2026 live scores fixtures {date_human}",
            f"World Cup 2026 matches {tomorrow} kickoff MSK",
        ]

    async def _fetch_and_pick(self) -> dict | None:
        if settings.ai_mock:
            future = now_msk().replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)
            return self._normalize_match(
                {
                    "home_team": "South Africa",
                    "away_team": "Canada",
                    "league": "FIFA World Cup 2026",
                    "kickoff_msk": format_datetime_msk(future),
                    "kickoff_at": future.isoformat(),
                    "teaser": "Mock fixture",
                }
            )

        now = now_msk()
        queries = self._build_queries(now)
        payload = await self.search.enrich(queries[:4])
        if not payload.results:
            logger.warning("Match of day search returned no results")
            return None

        parsed = pick_fixture_from_search(payload.results)
        if parsed:
            normalized = self._normalize_match(parsed)
            if normalized:
                logger.info(
                    "Match of day from search parser: %s vs %s",
                    normalized["home_team"],
                    normalized["away_team"],
                )
                return normalized

        search_json = json.dumps(
            [{"title": r.title, "snippet": r.snippet, "url": r.url} for r in payload.results[:16]],
            ensure_ascii=False,
        )
        ai_match = await self._pick_with_ai(search_json, now)
        if ai_match:
            return ai_match

        if parsed:
            return self._normalize_match(parsed)
        return None

    async def refresh_cache(self) -> MatchOfDayOut:
        redis = await get_redis()
        acquired = await redis.set(REFRESH_LOCK_KEY, "1", nx=True, ex=REFRESH_LOCK_TTL)
        if not acquired:
            cached = await redis.get(self._cache_key())
            if cached:
                data = json.loads(cached)
                return MatchOfDayOut(**data, cached=True)
            return EMPTY_MATCH

        try:
            match = await self._fetch_and_pick()
            key = self._cache_key()
            if match:
                await redis.setex(key, CACHE_TTL, json.dumps(match))
                logger.info("Match of day cached: %s vs %s (live=%s)", match["home_team"], match["away_team"], match["is_live"])
                return MatchOfDayOut(**match, cached=False)

            await redis.setex(
                key,
                EMPTY_CACHE_TTL,
                json.dumps({**EMPTY_MATCH.model_dump(), "cached": False}),
            )
            logger.warning("Match of day: no valid fixture found")
            return EMPTY_MATCH
        finally:
            await redis.delete(REFRESH_LOCK_KEY)

    async def get_match(self) -> MatchOfDayOut:
        """Read cached match only — no AI/search on user request."""
        redis = await get_redis()
        key = self._cache_key()
        cached = await redis.get(key)
        if cached:
            data = json.loads(cached)
            kickoff_dt = None
            if data.get("kickoff_at"):
                try:
                    kickoff_dt = datetime.fromisoformat(data["kickoff_at"])
                except ValueError:
                    kickoff_dt = parse_kickoff_msk(data.get("kickoff_msk", ""))
            if data.get("home_team") == "—" or not kickoff_dt:
                return MatchOfDayOut(**data, cached=True)
            if kickoff_dt and not is_kickoff_expired(kickoff_dt, live_buffer_minutes=130):
                data["is_live"] = kickoff_dt <= now_msk() < kickoff_dt + timedelta(minutes=130)
                return MatchOfDayOut(**data, cached=True)
            await redis.delete(key)

        return EMPTY_MATCH
