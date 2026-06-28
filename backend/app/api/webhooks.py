from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_internal_auth
from app.core.security import verify_tribute_signature
from app.schemas import NotifyRequest, UserOut
from app.services.funnel import FunnelService
from app.services.postback import PostbackService
from app.services.settings import SettingsService
from app.services.telegram_notify import TelegramNotify
from app.services.tribute import TributeService

router = APIRouter(prefix="/api/webhook", tags=["webhooks"])
payments_router = APIRouter(prefix="/api/payments", tags=["payments"])
notify = TelegramNotify()


def _extract_telegram_id(request: Request) -> int | None:
    params = dict(request.query_params)
    for key in ("sub1", "sub_id", "click_id", "telegram_id"):
        if key in params and str(params[key]).isdigit():
            return int(params[key])
    return None


def _extract_amount(request: Request) -> float | None:
    params = dict(request.query_params)
    for key in ("amount", "sum", "deposit"):
        if key in params:
            try:
                return float(params[key])
            except ValueError:
                pass
    return None


@router.api_route("/postback/registration", methods=["GET", "POST"])
async def postback_registration(request: Request, db: AsyncSession = Depends(get_db)):
    telegram_id = _extract_telegram_id(request)
    if not telegram_id:
        return {"ok": False, "error": "telegram_id not found"}
    payload = {"query": dict(request.query_params), "method": request.method}
    svc = PostbackService(db)
    user, is_new = await svc.handle_registration(telegram_id, payload)
    if is_new:
        await notify.report_registration(db, user=user, telegram_id=telegram_id)
    return {"ok": True, "telegram_id": telegram_id, "funnel_state": user.funnel_state if user else None}


@router.api_route("/postback/deposit", methods=["GET", "POST"])
async def postback_deposit(request: Request, db: AsyncSession = Depends(get_db)):
    telegram_id = _extract_telegram_id(request)
    if not telegram_id:
        return {"ok": False, "error": "telegram_id not found"}
    amount = _extract_amount(request)
    payload = {"query": dict(request.query_params), "method": request.method}
    svc = PostbackService(db)
    user, is_new = await svc.handle_deposit(telegram_id, amount, payload)
    if is_new:
        await notify.report_deposit(db, user=user, telegram_id=telegram_id, amount=amount)
    return {"ok": True, "telegram_id": telegram_id, "funnel_state": user.funnel_state if user else None}


@router.post("/tribute")
async def tribute_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("trbt-signature", "")
    secret = (
        await SettingsService(db).get("tribute_webhook_secret", "")
        or settings.tribute_webhook_secret
        or settings.tribute_api_key
    )
    if secret and not verify_tribute_signature(body, signature, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    import json

    data = json.loads(body)
    event_name = data.get("name") or data.get("event") or ""
    payload = data.get("payload") or data
    svc = TributeService(db)
    await svc.process_webhook(event_name, payload)
    return {"ok": True}


@payments_router.post("/unlimited/create", response_model=dict)
async def create_unlimited_payment(
    telegram_id: int = Depends(require_internal_auth),
    db: AsyncSession = Depends(get_db),
):
    if telegram_id is None:
        return {"error": "unauthorized"}
    funnel = FunnelService(db)
    user = await funnel.get_or_create(telegram_id)
    settings_svc = __import__("app.services.settings", fromlist=["SettingsService"]).SettingsService(db)
    amount = await settings_svc.get_int("unlimited_price_amount", 4900)
    currency = await settings_svc.get("unlimited_price_currency", "rub")
    title = "AI Analysis — Unlimited"
    try:
        svc = TributeService(db)
        return await svc.create_order(user, title, amount, currency)
    except RuntimeError as e:
        return {"error": str(e), "fallback": "contact_admin"}


@payments_router.get("/unlimited/status")
async def unlimited_status(
    telegram_id: int = Depends(require_internal_auth),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.models import TributePayment

    if telegram_id is None:
        return {"error": "unauthorized"}
    result = await db.execute(
        select(TributePayment)
        .where(TributePayment.telegram_id == telegram_id)
        .order_by(TributePayment.created_at.desc())
        .limit(1)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        return {"status": "none"}
    return {"status": payment.status, "order_uuid": payment.order_uuid}
