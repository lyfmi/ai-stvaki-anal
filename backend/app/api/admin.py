from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_admin, require_internal_auth
from app.schemas import (
    AdminStatsOut,
    AffiliateUpdate,
    BroadcastCreate,
    NotifyRequest,
    PaymentCreateOut,
    SettingsUpdate,
    UnlimitedGrant,
    UserOut,
)
from app.services.funnel import FunnelService
from app.services.settings import SettingsService
from app.services.translations import StatsService
from app.services.tribute import TributeService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsOut)
async def admin_stats(
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stats = await StatsService(db).get_stats()
    return AdminStatsOut(**stats)


@router.put("/settings")
async def update_settings(
    body: SettingsUpdate,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = SettingsService(db)
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    await svc.update_many(updates)
    return await svc.get_all()


@router.put("/affiliate")
async def update_affiliate(
    body: AffiliateUpdate,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = SettingsService(db)
    await svc.set("affiliate_ref_url", body.ref_url)
    await svc.set("affiliate_promo_code", body.promo_code)
    return {"ref_url": body.ref_url, "promo_code": body.promo_code}


@router.post("/unlimited/grant", response_model=UserOut)
async def grant_unlimited(
    body: UnlimitedGrant,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    funnel = FunnelService(db)
    user = await funnel.get_or_create(body.telegram_id)
    return await funnel.grant_unlimited(user)


@router.post("/unlimited/revoke", response_model=UserOut)
async def revoke_unlimited(
    body: UnlimitedGrant,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    funnel = FunnelService(db)
    user = await funnel.get_or_create(body.telegram_id)
    return await funnel.revoke_unlimited(user)


@router.post("/broadcast")
async def create_broadcast(
    body: BroadcastCreate,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models import Broadcast

    broadcast = Broadcast(
        admin_telegram_id=admin_id,
        message_text=body.text,
        photo_url=body.photo_url,
    )
    db.add(broadcast)
    await db.flush()
    return {"id": str(broadcast.id), "status": "queued"}


@router.get("/postback-urls")
async def postback_urls(_: int = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    base = settings.public_base_url.rstrip("/")
    svc = SettingsService(db)
    sub_param = await svc.get("affiliate_sub_param", "sub1")
    return {
        "registration": f"{base}/api/webhook/postback/registration?{sub_param}={{telegram_id}}",
        "deposit": f"{base}/api/webhook/postback/deposit?{sub_param}={{telegram_id}}&amount={{sum}}",
    }


@router.get("/users")
async def list_users(
    page: int = 1,
    search: str | None = None,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import or_, select

    from app.models import User

    q = select(User)
    if search:
        if search.isdigit():
            q = q.where(User.telegram_id == int(search))
        else:
            q = q.where(or_(User.username.ilike(f"%{search}%")))
    q = q.order_by(User.created_at.desc()).offset((page - 1) * 50).limit(50)
    result = await db.execute(q)
    users = result.scalars().all()
    return [UserOut.model_validate(u) for u in users]
