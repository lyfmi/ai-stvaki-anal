from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_internal_auth, require_internal_service
from app.schemas import NotifyRequest, UserOut
from app.services.admin import AdminService
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
    user = await funnel.get_or_create(telegram_id)
    admin_svc = AdminService(db)
    if await admin_svc.is_admin(telegram_id):
        user = await funnel.ensure_full_access(user)
    return await admin_svc.enrich_user(user)


@router.get("/settings")
async def get_settings(_: None = Depends(require_internal_service), db: AsyncSession = Depends(get_db)):
    svc = SettingsService(db)
    return await svc.get_all()


@router.get("/translations/{locale}")
async def get_translations(
    locale: str,
    _: None = Depends(require_internal_service),
    db: AsyncSession = Depends(get_db),
):
    svc = TranslationService(db)
    return await svc.get_many(locale)


@router.post("/notify")
async def notify(_: NotifyRequest, __: None = Depends(require_internal_service)):
    return {"ok": True, "note": "Bot handles notifications directly"}
