from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_internal_auth
from app.schemas import NotifyRequest, UserOut
from app.services.funnel import FunnelService
from app.services.settings import SettingsService
from app.services.translations import TranslationService

router = APIRouter(prefix="/api/internal", tags=["internal"])


@router.get("/user/{telegram_id}", response_model=UserOut)
async def get_user(
    telegram_id: int,
    _: int | None = Depends(require_internal_auth),
    db: AsyncSession = Depends(get_db),
):
    funnel = FunnelService(db)
    return await funnel.get_or_create(telegram_id)


@router.get("/settings")
async def get_settings(_: int | None = Depends(require_internal_auth), db: AsyncSession = Depends(get_db)):
    svc = SettingsService(db)
    return await svc.get_all()


@router.get("/translations/{locale}")
async def get_translations(locale: str, _: int | None = Depends(require_internal_auth), db: AsyncSession = Depends(get_db)):
    svc = TranslationService(db)
    return await svc.get_many(locale)


@router.post("/notify")
async def notify(_: NotifyRequest, __: int | None = Depends(require_internal_auth)):
    return {"ok": True, "note": "Bot handles notifications directly"}
