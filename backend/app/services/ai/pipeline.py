import json
import time

from app.core.config import settings
from app.schemas import AnalysisResult, SearchPayload, VisionPayload
from app.services.ai.prompts.synthesis import SYNTHESIS_SYSTEM_PROMPT, SYNTHESIS_USER_TEMPLATE
from app.services.ai.prompts.vision import VISION_SYSTEM_PROMPT, VISION_USER_PROMPT
from app.services.ai.providers.nous_client import NousClient
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
}

MOCK_SYNTHESIS = {
    "recommendation": "П1 — Победа Arsenal",
    "market": "1X2",
    "coefficient": 1.92,
    "probability_percent": 68,
    "risk": "medium",
    "arguments": ["Arsenal strong home form", "Chelsea missing key striker"],
    "confidence": "medium",
    "explanation": "Arsenal выглядит фаворитом дома. Chelsea ослаблена травмами.",
}


class VisionExtractor:
    def __init__(self) -> None:
        self.client = NousClient()

    async def extract(self, image_bytes: bytes, filename: str = "photo.jpg") -> VisionPayload:
        if settings.ai_mock:
            return VisionPayload.model_validate(MOCK_VISION)
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "jpg"
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(
            ext, "image/jpeg"
        )
        data = await self.client.vision_json(image_bytes, VISION_SYSTEM_PROMPT, VISION_USER_PROMPT, mime_type=mime)
        return VisionPayload.model_validate(data)


class Synthesizer:
    def __init__(self) -> None:
        self.client = NousClient()

    async def synthesize(
        self, vision: VisionPayload, search: SearchPayload, user_lang: str
    ) -> AnalysisResult:
        if settings.ai_mock:
            return AnalysisResult.model_validate(MOCK_SYNTHESIS)

        user_prompt = SYNTHESIS_USER_TEMPLATE.format(
            lang=user_lang,
            vision_json=json.dumps(vision.model_dump(), ensure_ascii=False),
            search_json=json.dumps(search.model_dump(), ensure_ascii=False),
        )
        data = await self.client.text_json(SYNTHESIS_SYSTEM_PROMPT, user_prompt)
        result = AnalysisResult.model_validate(data)
        if search.search_status == "failed":
            result.confidence = "low" if result.confidence == "high" else result.confidence
        return result


class AiAnalysisPipeline:
    def __init__(self) -> None:
        self.vision_extractor = VisionExtractor()
        self.search_enricher = SearchEnricher()
        self.synthesizer = Synthesizer()

    async def analyze_screenshot(self, image_bytes: bytes, user_lang: str, filename: str = "photo.jpg") -> dict:
        latencies: dict[str, int] = {}
        total_start = time.perf_counter()

        t0 = time.perf_counter()
        vision = await self.vision_extractor.extract(image_bytes, filename=filename)
        latencies["vision"] = int((time.perf_counter() - t0) * 1000)

        if vision.parse_confidence == "failed":
            raise UnreadableScreenshotError("Screenshot is unreadable")

        t0 = time.perf_counter()
        search = await self.search_enricher.enrich(vision.search_queries)
        latencies["search"] = int((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        result = await self.synthesizer.synthesize(vision, search, user_lang)
        latencies["synthesis"] = int((time.perf_counter() - t0) * 1000)
        latencies["total"] = int((time.perf_counter() - total_start) * 1000)

        return {
            "vision": vision,
            "search": search,
            "result": result,
            "pipeline_version": settings.ai_pipeline_version,
            "latency_ms": latencies,
        }
