import logging
import uuid
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import AiAnalysis, User
from app.schemas import SearchPayload, VisionPayload
from app.services.ai.match_context import resolve_match_context
from app.services.ai.pipeline import AiAnalysisPipeline, UnreadableScreenshotError, _looks_truncated
from app.services.ai.normalize import coerce_premium_insights
from app.services.analysis_mapper import analysis_to_detail, analysis_to_out, persist_analysis_fields
from app.services.funnel import FunnelService
from app.services.limits import AttemptsLimitService
from app.services.match_of_day import MatchOfDayService

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pipeline = AiAnalysisPipeline()
        self.limits = AttemptsLimitService(db)
        self.funnel = FunnelService(db)
        self.match_of_day = MatchOfDayService()

    async def _ensure_can_analyze(self, user: User, telegram_id: int) -> None:
        if not await self.funnel.can_analyze_funnel(user, telegram_id):
            raise PermissionError("Funnel not completed")
        can, _, _ = await self.limits.can_analyze(user)
        if not can:
            raise PermissionError("Daily limit exceeded")

    async def _finalize_attempt(self, user: User) -> None:
        await self.limits.consume_attempt(user)
        if user.has_unlimited:
            user.funnel_state = "UNLIMITED"
        elif user.funnel_state == "LIMIT_EXCEEDED":
            pass
        elif user.is_deposited:
            user.funnel_state = "ACTIVE"

    async def analyze(
        self, user: User, image_bytes: bytes, filename: str, telegram_id: int
    ) -> AiAnalysis:
        await self._ensure_can_analyze(user, telegram_id)

        storage_dir = Path(settings.storage_path) / "screenshots"
        storage_dir.mkdir(parents=True, exist_ok=True)
        image_id = uuid.uuid4()
        ext = Path(filename).suffix or ".jpg"
        image_path = storage_dir / f"{image_id}{ext}"
        image_path.write_bytes(image_bytes)

        # #region agent log
        from app.services.debug_agent_log import agent_log

        try:
            from PIL import Image
            import io

            with Image.open(io.BytesIO(image_bytes)) as img:
                agent_log(
                    location="analysis.py:analyze",
                    message="screenshot received",
                    data={"bytes": len(image_bytes), "w": img.width, "h": img.height, "filename": filename},
                    hypothesis_id="H4",
                    run_id="crop-fix",
                )
        except Exception:
            agent_log(
                location="analysis.py:analyze",
                message="screenshot received (no dims)",
                data={"bytes": len(image_bytes), "filename": filename},
                hypothesis_id="H4",
                run_id="crop-fix",
            )
        # #endregion

        try:
            pipeline_result = await self.pipeline.analyze_screenshot(
                image_bytes, user.language, filename=filename
            )
        except UnreadableScreenshotError as e:
            raise ValueError(str(e)) from e
        except ValidationError as e:
            raise ValueError("Не удалось распознать скриншот") from e
        except RuntimeError as e:
            msg = str(e)
            if "Vision" in msg or "vision" in msg:
                raise ValueError("Не удалось прочитать скриншот") from e
            if "JSON" in msg or "synthesis" in msg.lower():
                raise ValueError("Ошибка AI-анализа, попробуйте ещё раз") from e
            raise ValueError("Ошибка обработки, попробуйте ещё раз") from e

        vision = pipeline_result["vision"]
        search = pipeline_result["search"]
        result = pipeline_result["result"]

        analysis = AiAnalysis(
            user_id=user.id,
            image_path=str(image_path),
            source_type="screenshot",
            vision_payload=vision.model_dump(),
            search_payload=search.model_dump(),
            pipeline_version=pipeline_result["pipeline_version"],
            latency_ms=pipeline_result["latency_ms"],
        )
        persist_analysis_fields(analysis, result)
        self.db.add(analysis)

        await self._finalize_attempt(user)
        await self.db.flush()
        return analysis

    async def predict_match_of_day(self, user: User, telegram_id: int) -> AiAnalysis:
        await self._ensure_can_analyze(user, telegram_id)

        match = await self.match_of_day.get_match()
        if not match.home_team or match.home_team == "—":
            raise ValueError("Нет актуального матча дня")

        match_dict = match.model_dump(exclude={"cached"})

        try:
            pipeline_result = await self.pipeline.analyze_match_of_day(match_dict, user.language)
        except ValidationError as e:
            raise ValueError("Ошибка AI-анализа, попробуйте ещё раз") from e
        except RuntimeError as e:
            # #region agent log
            from app.services.debug_agent_log import agent_log

            agent_log(
                location="analysis.py:predict_match_of_day",
                message="pipeline runtime error",
                data={"error": str(e), "match": match_dict.get("home_team")},
                hypothesis_id="F",
            )
            # #endregion
            raise ValueError("Ошибка AI-анализа, попробуйте ещё раз") from e

        search = pipeline_result["search"]
        result = pipeline_result["result"]

        analysis = AiAnalysis(
            user_id=user.id,
            image_path=None,
            source_type="match_of_day",
            vision_payload={"match_of_day": match_dict},
            search_payload=search.model_dump(),
            pipeline_version=pipeline_result["pipeline_version"],
            latency_ms=pipeline_result["latency_ms"],
        )
        persist_analysis_fields(analysis, result)
        self.db.add(analysis)

        await self._finalize_attempt(user)
        await self.db.flush()
        return analysis

    async def list_for_user(self, user: User, limit: int = 20) -> list[AiAnalysis]:
        result = await self.db.execute(
            select(AiAnalysis)
            .where(AiAnalysis.user_id == user.id)
            .order_by(AiAnalysis.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, user: User, analysis_id: uuid.UUID) -> AiAnalysis | None:
        result = await self.db.execute(
            select(AiAnalysis).where(AiAnalysis.id == analysis_id, AiAnalysis.user_id == user.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return await self.repair_if_needed(user, row)

    async def repair_if_needed(self, user: User, analysis: AiAnalysis) -> AiAnalysis:
        unlimited = user.has_unlimited or user.funnel_state == "UNLIMITED"
        if not unlimited:
            return analysis

        raw = analysis.raw_ai_response or {}
        premium = coerce_premium_insights(analysis.premium_payload) or coerce_premium_insights(
            raw.get("premium_insights")
        )
        premium_incomplete = premium is None or not (
            premium.form_bars or premium.key_stats or premium.h2h
        )
        if not _looks_truncated(raw) and not premium_incomplete:
            return analysis

        try:
            if analysis.source_type == "match_of_day":
                match = (analysis.vision_payload or {}).get("match_of_day") or {}
                search = SearchPayload.model_validate(analysis.search_payload or {"results": []})
                result = await self.pipeline.synthesizer.synthesize_match_of_day(
                    match, search, user.language
                )
            else:
                vision = VisionPayload.model_validate(analysis.vision_payload or {})
                search = SearchPayload.model_validate(analysis.search_payload or {"results": []})
                match_context = resolve_match_context(vision, search, user_lang=user.language)
                result = await self.pipeline.synthesizer.synthesize(
                    vision, search, user.language, match_context=match_context
                )
            persist_analysis_fields(analysis, result)
            await self.db.flush()
            logger.info("Repaired truncated analysis %s for user %s", analysis.id, user.id)
        except Exception as exc:
            logger.warning("Analysis repair failed for %s: %s", analysis.id, exc)
        return analysis

    @staticmethod
    def to_out(row: AiAnalysis):
        return analysis_to_out(row)

    @staticmethod
    def to_detail(row: AiAnalysis):
        return analysis_to_detail(row)
