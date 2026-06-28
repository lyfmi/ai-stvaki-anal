from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_internal_auth
from app.schemas import (
    AnalysisDetailOut,
    AnalysisOut,
    LanguageUpdate,
    PaymentCreateOut,
    UserOut,
    UserStatusOut,
)
from app.services.analysis import AnalysisService
from app.services.funnel import FunnelService
from app.services.limits import AttemptsLimitService
from app.services.settings import SettingsService
from app.services.tribute import TributeService

router = APIRouter(prefix="/api/user", tags=["user"])


async def _get_user(
    telegram_id: int = Depends(require_internal_auth),
    db: AsyncSession = Depends(get_db),
):
    if telegram_id is None:
        raise HTTPException(status_code=401, detail="X-Telegram-User-Id required")
    funnel = FunnelService(db)
    return await funnel.get_or_create(telegram_id)


@router.get("/me", response_model=UserOut)
async def get_me(user=Depends(_get_user)):
    return user


@router.get("/status", response_model=UserStatusOut)
async def get_status(user=Depends(_get_user), db: AsyncSession = Depends(get_db)):
    limits = AttemptsLimitService(db)
    funnel = FunnelService(db)
    can_analyze_limit, remaining, reset_at = await limits.can_analyze(user)
    can_funnel = funnel.can_analyze_funnel(user, user.telegram_id)
    daily_limit = await limits.get_daily_limit()
    return UserStatusOut(
        user=user,
        can_analyze=can_funnel and (can_analyze_limit or user.telegram_id in settings.admin_ids),
        attempts_remaining=remaining if not user.has_unlimited else 999999,
        attempts_reset_at=reset_at,
        daily_limit=daily_limit,
    )


@router.post("/language", response_model=UserOut)
async def set_language(body: LanguageUpdate, user=Depends(_get_user), db: AsyncSession = Depends(get_db)):
    funnel = FunnelService(db)
    return await funnel.set_language(user, body.language)


@router.post("/check-subscription", response_model=UserOut)
async def check_subscription(user=Depends(_get_user), db: AsyncSession = Depends(get_db)):
    funnel = FunnelService(db)
    settings_svc = SettingsService(db)
    channel_id = await settings_svc.get("channel_id")
    if not channel_id:
        return await funnel.mark_channel_subscribed(user)
    return user


@router.post("/analyze", response_model=AnalysisOut)
async def analyze_screenshot(
    screenshot: UploadFile = File(...),
    user=Depends(_get_user),
    db: AsyncSession = Depends(get_db),
    telegram_id: int = Depends(require_internal_auth),
):
    if telegram_id is None:
        raise HTTPException(status_code=401, detail="X-Telegram-User-Id required")
    content = await screenshot.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    svc = AnalysisService(db)
    try:
        analysis = await svc.analyze(user, content, screenshot.filename or "photo.jpg", telegram_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return analysis


@router.get("/analyses", response_model=list[AnalysisOut])
async def list_analyses(user=Depends(_get_user), db: AsyncSession = Depends(get_db)):
    svc = AnalysisService(db)
    return await svc.list_for_user(user)


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetailOut)
async def get_analysis(analysis_id: str, user=Depends(_get_user), db: AsyncSession = Depends(get_db)):
    import uuid

    svc = AnalysisService(db)
    analysis = await svc.get_by_id(user, uuid.UUID(analysis_id))
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/settings", response_model=dict[str, str])
async def get_public_settings(user=Depends(_get_user), db: AsyncSession = Depends(get_db)):
    svc = SettingsService(db)
    return await svc.get_all()
