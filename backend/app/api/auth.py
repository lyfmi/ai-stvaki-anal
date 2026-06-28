from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_telegram_init_data
from app.schemas import AuthTelegramRequest, AuthTelegramResponse, UserOut
from app.services.funnel import FunnelService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/telegram", response_model=AuthTelegramResponse)
async def auth_telegram(body: AuthTelegramRequest, db: AsyncSession = Depends(get_db)):
    parsed = verify_telegram_init_data(body.init_data, settings.bot_token)
    if not parsed:
        raise HTTPException(status_code=401, detail="Invalid initData")
    user_data = parsed.get("user") or {}
    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="No user in initData")
    funnel = FunnelService(db)
    user = await funnel.get_or_create(telegram_id, username=user_data.get("username"))
    token = f"stub-jwt-{telegram_id}"
    return AuthTelegramResponse(token=token, user=UserOut.model_validate(user))
