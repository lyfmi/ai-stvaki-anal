import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import AiAnalysis, User
from app.services.ai.pipeline import AiAnalysisPipeline, UnreadableScreenshotError
from app.services.funnel import FunnelService
from app.services.limits import AttemptsLimitService


class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pipeline = AiAnalysisPipeline()
        self.limits = AttemptsLimitService(db)
        self.funnel = FunnelService(db)

    async def analyze(
        self, user: User, image_bytes: bytes, filename: str, telegram_id: int
    ) -> AiAnalysis:
        if not self.funnel.can_analyze_funnel(user, telegram_id):
            raise PermissionError("Funnel not completed")

        can, remaining, _ = await self.limits.can_analyze(user)
        if not can and telegram_id not in settings.admin_ids:
            raise PermissionError("Daily limit exceeded")

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
        except RuntimeError as e:
            raise ValueError("AI analysis failed") from e

        vision = pipeline_result["vision"]
        search = pipeline_result["search"]
        result = pipeline_result["result"]

        analysis = AiAnalysis(
            user_id=user.id,
            image_path=str(image_path),
            recommendation=result.recommendation,
            coefficient=result.coefficient,
            probability_percent=result.probability_percent,
            explanation=result.explanation,
            risk=result.risk,
            confidence=result.confidence,
            arguments=result.arguments,
            vision_payload=vision.model_dump(),
            search_payload=search.model_dump(),
            pipeline_version=pipeline_result["pipeline_version"],
            latency_ms=pipeline_result["latency_ms"],
            raw_ai_response=result.model_dump(),
        )
        self.db.add(analysis)

        if telegram_id not in settings.admin_ids:
            await self.limits.consume_attempt(user)
            if user.has_unlimited:
                user.funnel_state = "UNLIMITED"
            elif user.funnel_state == "LIMIT_EXCEEDED":
                pass
            elif user.is_deposited:
                user.funnel_state = "ACTIVE"

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
