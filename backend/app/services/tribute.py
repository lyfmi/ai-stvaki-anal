import hashlib
import json
import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import TributePayment, User
from app.services.funnel import FunnelService
from app.services.telegram_notify import TelegramNotify


class TributeService:
    TRIBUTE_API = "https://tribute.tg/api/v1"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.funnel = FunnelService(db)
        self.notify = TelegramNotify()

    async def create_order(self, user: User, title: str, amount: int, currency: str) -> dict:
        if not settings.tribute_api_key:
            raise RuntimeError("TRIBUTE_API_KEY is not configured")

        payload = {
            "title": title,
            "description": "Unlimited AI analysis access",
            "amount": amount,
            "currency": currency.lower(),
            "period": "onetime",
            "customerId": str(user.telegram_id),
            "successUrl": f"{settings.public_base_url}/payment/success",
            "failUrl": f"{settings.public_base_url}/payment/fail",
            "comment": "unlimited_purchase",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.TRIBUTE_API}/shop/orders",
                headers={"Api-Key": settings.tribute_api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        order_uuid = data.get("uuid") or str(uuid.uuid4())
        payment = TributePayment(
            order_uuid=order_uuid,
            telegram_id=user.telegram_id,
            amount=amount,
            currency=currency,
            status=data.get("status", "pending"),
            raw_payload=data,
        )
        self.db.add(payment)
        await self.db.flush()
        return {
            "order_uuid": order_uuid,
            "webapp_payment_url": data.get("webappPaymentUrl"),
            "payment_url": data.get("paymentUrl"),
            "amount": amount,
            "currency": currency,
        }

    async def get_by_order_uuid(self, order_uuid: str) -> TributePayment | None:
        result = await self.db.execute(select(TributePayment).where(TributePayment.order_uuid == order_uuid))
        return result.scalar_one_or_none()

    async def process_webhook(self, event_name: str, payload: dict) -> bool:
        order_uuid = payload.get("uuid") or payload.get("order_uuid")
        customer_id = payload.get("customerId") or payload.get("telegram_user_id")
        if not customer_id:
            return False

        telegram_id = int(customer_id)
        if order_uuid:
            existing = await self.get_by_order_uuid(order_uuid)
            if existing and existing.status == "paid" and event_name in (
                "shopOrderPaymentReceived",
                "shopOrder",
                "new_digital_product",
            ):
                return True

        result = await self.db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        grant_events = {"shopOrderPaymentReceived", "shopOrder", "new_digital_product"}
        revoke_events = {"shopOrderRefunded", "digitalProductRefund"}

        if event_name in grant_events:
            status = payload.get("status", "paid")
            if event_name == "shopOrder" and status != "paid":
                return True
            await self.funnel.grant_unlimited(user)
            if order_uuid:
                payment = await self.get_by_order_uuid(order_uuid)
                if payment:
                    payment.status = "paid"
                    payment.raw_payload = payload
                    payment.updated_at = datetime.now(UTC)
                else:
                    self.db.add(
                        TributePayment(
                            order_uuid=order_uuid,
                            telegram_id=telegram_id,
                            amount=payload.get("amount"),
                            currency=payload.get("currency"),
                            status="paid",
                            raw_payload=payload,
                        )
                    )
            await self.notify.report_unlimited_paid(
                self.db,
                user=user,
                telegram_id=telegram_id,
                amount=payload.get("amount"),
                currency=payload.get("currency"),
                order_uuid=order_uuid,
            )
            return True

        if event_name in revoke_events:
            await self.funnel.revoke_unlimited(user)
            if order_uuid:
                payment = await self.get_by_order_uuid(order_uuid)
                if payment:
                    payment.status = "refunded"
                    payment.raw_payload = payload
            await self.notify.report_unlimited_refund(
                self.db,
                user=user,
                telegram_id=telegram_id,
                order_uuid=order_uuid,
            )
            return True

        if event_name == "shopOrderPaymentFailed":
            if order_uuid:
                payment = await self.get_by_order_uuid(order_uuid)
                if payment:
                    payment.status = "failed"
                    payment.raw_payload = payload
            await self.notify.report_payment_failed(
                self.db,
                telegram_id=telegram_id,
                order_uuid=order_uuid,
            )
            return True

        return True
