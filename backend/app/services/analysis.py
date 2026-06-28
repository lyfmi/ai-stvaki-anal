import uuid
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import AiAnalysis, User
from app.services.ai.pipeline import AiAnalysisPipeline, UnreadableScreenshotError
from app.services.analysis_mapper import analysis_to_detail, analysis_to_out, persist_analysis_fields
from app.services.funnel import FunnelService
from app.services.limits import AttemptsLimitService
from app.services.match_of_day import MatchOfDayService


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

        try:
            pipeline_result = await self.pipeline.analyze_screenshot(
                image_bytes, user.language, filename=filename
            )
        except UnreadableScreenshotError as e:
            raise ValueError(str(e)) from e
        except (RuntimeError, ValidationError) as e:
            raise ValueError("AI analysis failed") from e

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
        match_dict = match.model_dump(exclude={"cached"})

        try:
            pipeline_result = await self.pipeline.analyze_match_of_day(match_dict, user.language)
        except (RuntimeError, ValidationError) as e:
            raise ValueError("AI analysis failed") from e

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
        return result.scalar_one_or_none()

    @staticmethod
    def to_out(row: AiAnalysis):
        return analysis_to_out(row)

    @staticmethod
    def to_detail(row: AiAnalysis):
        return analysis_to_detail(row)
