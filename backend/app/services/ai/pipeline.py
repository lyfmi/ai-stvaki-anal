import json
import time

from pydantic import ValidationError

from app.core.config import settings
from app.schemas import AnalysisResult, SearchPayload, VisionPayload
from app.services.ai.match_context import resolve_match_context, resolve_match_context_from_fixture
from app.services.ai.normalize import apply_post_match_overrides, parse_analysis_result
from app.services.ai.prompts.synthesis import (
    COMPACT_SYNTHESIS_SYSTEM_PROMPT,
    MATCH_OF_DAY_COMPACT_TEMPLATE,
    MATCH_OF_DAY_SYNTHESIS_TEMPLATE,
    POST_MATCH_COMPACT_TEMPLATE,
    SYNTHESIS_SYSTEM_PROMPT,
    SYNTHESIS_USER_TEMPLATE,
)
from app.services.ai.prompts.vision import VISION_SYSTEM_PROMPT, VISION_USER_PROMPT
from app.services.ai.providers.groq_client import GroqClient
from app.services.ai.rag_search import build_rag_queries_for_fixture, build_rag_queries_for_vision
from app.services.ai.search_enricher import SearchEnricher


class UnreadableScreenshotError(Exception):
    pass


MOCK_VISION = {
    "sport": "football",
    "league": "Premier League",
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "match_datetime": None,
    "market_type": "1X2",
    "available_outcomes": [{"label": "П1", "coefficient": 1.92}, {"label": "X", "coefficient": 3.4}],
    "screenshot_notes": "mock data",
    "search_queries": ["Arsenal vs Chelsea lineups injuries", "Arsenal Chelsea head to head"],
    "parse_confidence": "high",
    "datetime_on_screenshot": False,
    "odds_on_screenshot": True,
    "match_status_hint": "upcoming",
}

MOCK_PREMATCH_SYNTHESIS = {
    "recommendation": "П1 — Победа Arsenal",
    "market": "1X2",
    "coefficient": 1.92,
    "probability_percent": 68,
    "risk": "medium",
    "arguments": ["Arsenal strong home form", "Chelsea missing key striker"],
    "confidence": "medium",
    "explanation": "На скриншоте не указано время проведения. Arsenal выглядит фаворитом дома.",
    "analysis_mode": "pre_match",
    "match_status_label": "Скоро",
    "match_datetime_msk": "28.06.2026 20:00 МСК",
    "is_betting_recommendation": True,
    "premium_insights": {
        "form_bars": [
            {"team": "Arsenal", "wins": 4, "draws": 1, "losses": 0},
            {"team": "Chelsea", "wins": 2, "draws": 2, "losses": 1},
        ],
        "h2h": "Последние 5 встреч: 2 победы Arsenal, 2 ничьи, 1 победа Chelsea",
        "key_stats": [{"label": "Голы/матч", "home": "2.1", "away": "1.4"}],
        "trends": ["Arsenal не проигрывает дома 8 матчей"],
        "advanced_arguments": ["Chelsea пропускает в 70% выездных матчей"],
    },
}

MOCK_POSTMATCH_SYNTHESIS = {
    "recommendation": "Победа Chelsea 1:2",
    "market": "1X2",
    "coefficient": None,
    "probability_percent": None,
    "risk": "medium",
    "arguments": ["Chelsea контролировала второй тайм", "Arsenal не реализовал моменты"],
    "confidence": "high",
    "explanation": "Матч уже завершён. Chelsea забила дважды во втором тайме после раннего гола Arsenal.",
    "analysis_mode": "post_match",
    "match_status_label": "Матч завершён",
    "match_datetime_msk": "27.06.2026 18:00 МСК",
    "is_betting_recommendation": False,
    "final_score": "1:2",
    "winner": "Chelsea",
    "premium_insights": MOCK_PREMATCH_SYNTHESIS["premium_insights"],
}


VISION_REPAIR_PROMPT = """Return ONLY valid JSON with keys:
sport, league, home_team, away_team, match_datetime, market_type, available_outcomes,
screenshot_notes, search_queries, parse_confidence, datetime_on_screenshot, odds_on_screenshot, match_status_hint.
Extract team names and match datetime from the screenshot. Odds optional."""


class VisionExtractor:
    def __init__(self) -> None:
        self.client = GroqClient()

    async def extract(
        self, image_bytes: bytes, filename: str = "photo.jpg", *, model: str | None = None
    ) -> VisionPayload:
        if settings.ai_mock:
            return VisionPayload.model_validate(MOCK_VISION)
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "jpg"
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(
            ext, "image/jpeg"
        )
        try:
            data = await self.client.vision_json(
                image_bytes, VISION_SYSTEM_PROMPT, VISION_USER_PROMPT, mime_type=mime, model=model
            )
            return VisionPayload.model_validate(data)
        except (ValidationError, RuntimeError):
            data = await self.client.vision_json(
                image_bytes,
                VISION_SYSTEM_PROMPT,
                f"{VISION_USER_PROMPT}\n\n{VISION_REPAIR_PROMPT}",
                mime_type=mime,
                model=model,
            )
            return VisionPayload.model_validate(data)


SYNTHESIS_REPAIR_PROMPT = """The previous JSON was invalid or truncated. Return ONLY one JSON object with keys:
recommendation, market, coefficient, probability_percent, risk, arguments, confidence, explanation,
analysis_mode, match_status_label, match_datetime_msk, is_betting_recommendation, premium_insights.
Keep arguments concise (max 2 short sentences each) but COMPLETE — no cut-off words.
recommendation must be a non-empty string."""


def _looks_truncated(data: dict) -> bool:
    if data.get("_finish_reason") == "length":
        return True
    for arg in data.get("arguments") or []:
        if isinstance(arg, str) and len(arg) > 20 and arg[-1].isalnum() and arg[-1] not in ".!?":
            tail = arg.split()[-1] if arg.split() else ""
            if len(tail) < 4:
                return True
    rec = str(data.get("recommendation") or "").strip()
    return len(rec) < 3


def _search_bullets(search: SearchPayload, limit: int = 4) -> str:
    lines: list[str] = []
    for item in search.results[:limit]:
        snippet = (item.snippet or "").replace("\n", " ")[:120]
        title = (item.title or "")[:80]
        if title or snippet:
            lines.append(f"- {title}: {snippet}".strip())
    return "\n".join(lines) if lines else "- limited data"


class Synthesizer:
    def __init__(self) -> None:
        self.client = GroqClient()

    async def _call_synthesis(
        self,
        user_prompt: str,
        *,
        mock_data: dict | None = None,
        model: str | None = None,
    ) -> AnalysisResult:
        if settings.ai_mock and mock_data:
            return AnalysisResult.model_validate(mock_data)

        token_limit = settings.groq_max_tokens
        data = await self.client.text_json(
            SYNTHESIS_SYSTEM_PROMPT, user_prompt, model=model, max_tokens=token_limit
        )
        try:
            result = parse_analysis_result(data)
        except (ValidationError, RuntimeError):
            repair_prompt = (
                f"{user_prompt}\n\nPrevious invalid JSON:\n{json.dumps(data, ensure_ascii=False)}\n\n"
                f"{SYNTHESIS_REPAIR_PROMPT}"
            )
            data = await self.client.text_json(
                SYNTHESIS_SYSTEM_PROMPT, repair_prompt, model=model, max_tokens=token_limit
            )
            result = parse_analysis_result(data)

        if _looks_truncated(data) or not (result.recommendation or "").strip():
            compact_prompt = (
                f"{user_prompt}\n\nPrevious response was truncated. Return compact but COMPLETE JSON. "
                "Use at most 2 short arguments. Fill premium_insights.form_bars and key_stats."
            )
            data = await self.client.text_json(
                COMPACT_SYNTHESIS_SYSTEM_PROMPT, compact_prompt, model=model, max_tokens=token_limit
            )
            result = parse_analysis_result(data)

        if not (result.recommendation or "").strip():
            raise RuntimeError("AI synthesis returned empty recommendation")
        return result

    async def synthesize(
        self,
        vision: VisionPayload,
        search: SearchPayload,
        user_lang: str,
        *,
        match_context=None,
        force_pre_match: bool = False,
        model: str | None = None,
    ) -> AnalysisResult:
        ctx = match_context or resolve_match_context(
            vision, search, user_lang=user_lang, force_pre_match=force_pre_match
        )

        mock = MOCK_PREMATCH_SYNTHESIS if ctx.analysis_mode != "post_match" else MOCK_POSTMATCH_SYNTHESIS

        if ctx.analysis_mode == "post_match":
            compact_prompt = POST_MATCH_COMPACT_TEMPLATE.format(
                lang=user_lang,
                home=vision.home_team or "",
                away=vision.away_team or "",
                match_status_label=ctx.match_status_label,
                final_score=vision.final_score or "unknown",
                winner=vision.winner or "unknown",
                search_bullets=_search_bullets(search),
            )
            data = await self.client.text_json(
                COMPACT_SYNTHESIS_SYSTEM_PROMPT,
                compact_prompt,
                model=model,
                max_tokens=settings.groq_max_tokens,
            )
            result = parse_analysis_result(data)
        else:
            user_prompt = SYNTHESIS_USER_TEMPLATE.format(
                lang=user_lang,
                match_context_json=json.dumps(ctx.model_dump(), ensure_ascii=False),
                vision_json=json.dumps(vision.model_dump(), ensure_ascii=False),
                search_json=json.dumps({"results": [r.model_dump() for r in search.results[:6]]}, ensure_ascii=False),
                analysis_mode=ctx.analysis_mode,
                match_status_label=ctx.match_status_label,
                match_datetime_msk=ctx.match_datetime_msk or "",
            )
            result = await self._call_synthesis(user_prompt, mock_data=mock, model=model)
        if search.search_status == "failed":
            result.confidence = "low" if result.confidence == "high" else result.confidence
        if not result.match_status_label:
            result.match_status_label = ctx.match_status_label
        if not result.analysis_mode:
            result.analysis_mode = ctx.analysis_mode
        if result.match_datetime_msk is None:
            result.match_datetime_msk = ctx.match_datetime_msk
        # Authoritative context overrides AI hallucinations on status/time
        result.match_status_label = ctx.match_status_label
        result.analysis_mode = ctx.analysis_mode
        if ctx.match_datetime_msk:
            result.match_datetime_msk = ctx.match_datetime_msk
        result = apply_post_match_overrides(result, vision=vision, ctx=ctx)
        return result

    async def synthesize_match_of_day(
        self,
        match: dict,
        search: SearchPayload,
        user_lang: str,
        *,
        model: str | None = None,
    ) -> AnalysisResult:
        ctx = resolve_match_context_from_fixture(match, user_lang=user_lang)
        compact_prompt = MATCH_OF_DAY_COMPACT_TEMPLATE.format(
            lang=user_lang,
            home=match.get("home_team", ""),
            away=match.get("away_team", ""),
            league=match.get("league", "Football"),
            kickoff=match.get("kickoff_msk") or ctx.match_datetime_msk or "",
            status=ctx.match_status_label,
            analysis_mode=ctx.analysis_mode,
            search_bullets=_search_bullets(search),
        )
        try:
            data = await self.client.text_json(
                COMPACT_SYNTHESIS_SYSTEM_PROMPT,
                compact_prompt,
                model=model,
                max_tokens=settings.groq_max_tokens,
            )
            result = parse_analysis_result(data)
        except (ValidationError, RuntimeError):
            user_prompt = MATCH_OF_DAY_SYNTHESIS_TEMPLATE.format(
                lang=user_lang,
                match_json=json.dumps(match, ensure_ascii=False),
                search_json=json.dumps({"results": [r.model_dump() for r in search.results[:6]]}, ensure_ascii=False),
                match_context_json=json.dumps(ctx.model_dump(), ensure_ascii=False),
            )
            mock = MOCK_PREMATCH_SYNTHESIS if ctx.analysis_mode != "post_match" else MOCK_POSTMATCH_SYNTHESIS
            result = await self._call_synthesis(user_prompt, mock_data=mock, model=model)

        result.analysis_mode = ctx.analysis_mode
        result.match_status_label = ctx.match_status_label
        result = apply_post_match_overrides(result, ctx=ctx)
        if ctx.match_datetime_msk:
            result.match_datetime_msk = ctx.match_datetime_msk
        elif match.get("kickoff_msk"):
            result.match_datetime_msk = match.get("kickoff_msk")
        return result


class AiAnalysisPipeline:
    def __init__(self) -> None:
        self.vision_extractor = VisionExtractor()
        self.search_enricher = SearchEnricher()
        self.synthesizer = Synthesizer()

    async def analyze_screenshot(
        self,
        image_bytes: bytes,
        user_lang: str,
        filename: str = "photo.jpg",
        *,
        model: str | None = None,
    ) -> dict:
        latencies: dict[str, int] = {}
        total_start = time.perf_counter()

        t0 = time.perf_counter()
        vision = await self.vision_extractor.extract(image_bytes, filename=filename, model=model)
        latencies["vision"] = int((time.perf_counter() - t0) * 1000)

        if vision.parse_confidence == "failed":
            raise UnreadableScreenshotError("Screenshot is unreadable")

        queries = build_rag_queries_for_vision(vision)
        t0 = time.perf_counter()
        search = await self.search_enricher.enrich(queries)
        latencies["search"] = int((time.perf_counter() - t0) * 1000)

        match_context = resolve_match_context(vision, search, user_lang=user_lang)

        t0 = time.perf_counter()
        result = await self.synthesizer.synthesize(
            vision, search, user_lang, match_context=match_context, model=model
        )
        latencies["synthesis"] = int((time.perf_counter() - t0) * 1000)
        latencies["total"] = int((time.perf_counter() - total_start) * 1000)

        return {
            "vision": vision,
            "search": search,
            "result": result,
            "match_context": match_context,
            "pipeline_version": settings.ai_pipeline_version,
            "latency_ms": latencies,
        }

    async def analyze_match_of_day(self, match: dict, user_lang: str, *, model: str | None = None) -> dict:
        latencies: dict[str, int] = {}
        total_start = time.perf_counter()

        queries = build_rag_queries_for_fixture(match)

        t0 = time.perf_counter()
        search = await self.search_enricher.enrich(queries)
        latencies["search"] = int((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        result = await self.synthesizer.synthesize_match_of_day(match, search, user_lang, model=model)
        latencies["synthesis"] = int((time.perf_counter() - t0) * 1000)
        latencies["total"] = int((time.perf_counter() - total_start) * 1000)

        return {
            "search": search,
            "result": result,
            "pipeline_version": settings.ai_pipeline_version,
            "latency_ms": latencies,
        }
