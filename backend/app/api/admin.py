from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_admin, require_internal_auth
from app.schemas import (
    AdminAdd,
    AdminOut,
    AdminRemove,
    AdminStatsOut,
    AffiliateUpdate,
    SettingsUpdate,
    UnlimitedGrant,
    UserOut,
)
from app.services.admin import AdminService
from app.services.broadcast import BroadcastService
from app.services.funnel import FunnelService
from app.services.settings import SettingsService
from app.services.translations import StatsService
from app.services.tribute import TributeService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/admins", response_model=list[AdminOut])
async def list_admins(
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService(db).list_admins()


@router.post("/admins", response_model=AdminOut)
async def add_admin(
    body: AdminAdd,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if body.telegram_id is None and not body.username:
        raise HTTPException(status_code=400, detail="telegram_id or username required")
    return await AdminService(db).add_admin(telegram_id=body.telegram_id, username=body.username)


@router.delete("/admins")
async def remove_admin(
    body: AdminRemove,
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await AdminService(db).remove_admin(body.telegram_id, admin_id)
    return {"ok": True}


@router.post("/users/activate", response_model=UserOut)
async def activate_user(
    body: UnlimitedGrant,
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    funnel = FunnelService(db)
    admin_svc = AdminService(db)
    user = await funnel.get_or_create(body.telegram_id)
    user.is_channel_subscribed = True
    if user.funnel_state == "NEW":
        user.funnel_state = "LANGUAGE_SELECTED"
    await funnel.mark_registered(user, admin_bypass=True)
    await funnel.mark_deposited(user, amount=0, admin_bypass=True)
    return await admin_svc.enrich_user(user)


@router.get("/stats", response_model=AdminStatsOut)
async def admin_stats(
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stats = await StatsService(db).get_stats()
    return AdminStatsOut(**stats)


@router.get("/settings")
async def get_admin_settings(
    _: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await SettingsService(db).get_all()


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
    text: str = Form(...),
    photos: list[UploadFile] = File(default=[]),
    admin_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    from pathlib import Path

    from app.models import Broadcast

    if len(photos) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 photos allowed")

    broadcast = Broadcast(
        admin_telegram_id=admin_id,
        message_text=text,
    )
    db.add(broadcast)
    await db.flush()

    photo_paths: list[str] = []
    if photos:
        storage_dir = Path(settings.storage_path) / "broadcasts" / str(broadcast.id)
        storage_dir.mkdir(parents=True, exist_ok=True)
        for idx, upload in enumerate(photos):
            content = await upload.read()
            if len(content) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Photo too large (max 10MB)")
            ext = Path(upload.filename or "photo.jpg").suffix or ".jpg"
            path = storage_dir / f"{idx}{ext}"
            path.write_bytes(content)
            photo_paths.append(str(path))
        broadcast.photo_paths = photo_paths

    try:
        sent, failed = await BroadcastService(db).run(broadcast)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "id": str(broadcast.id),
        "status": "completed",
        "sent_count": sent,
        "failed_count": failed,
    }


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
