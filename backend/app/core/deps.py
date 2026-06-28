from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models import User


async def require_internal_service(
    x_internal_secret: str | None = Header(None, alias="X-Internal-Secret"),
) -> None:
    if x_internal_secret is None or x_internal_secret != settings.internal_api_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal secret")


async def require_internal_auth(
    x_internal_secret: str | None = Header(None, alias="X-Internal-Secret"),
    x_telegram_user_id: int | None = Header(None, alias="X-Telegram-User-Id"),
    authorization: str | None = Header(None, alias="Authorization"),
    x_telegram_init_data: str | None = Header(None, alias="X-Telegram-Init-Data"),
) -> int:
    # 1. Internal secret check
    if x_internal_secret is not None:
        if x_internal_secret != settings.internal_api_secret:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal secret")
        if x_telegram_user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-Telegram-User-Id header required")
        return x_telegram_user_id

    # 2. Authorization Bearer check
    if authorization is not None:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            if token.startswith("stub-jwt-"):
                try:
                    return int(token.split("-")[-1])
                except ValueError:
                    pass
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Bearer token")

    # 3. Init data check
    if x_telegram_init_data is not None:
        from app.core.security import verify_telegram_init_data
        parsed = verify_telegram_init_data(x_telegram_init_data, settings.bot_token)
        if not parsed:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid init data")
        user_data = parsed.get("user") or {}
        telegram_id = user_data.get("id")
        if not telegram_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No user ID in init data")
        return telegram_id

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization credentials missing")


async def require_admin(
    telegram_id: int = Depends(require_internal_auth),
    db: AsyncSession = Depends(get_db),
) -> int:
    from app.services.admin import AdminService

    if not await AdminService(db).is_admin(telegram_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return telegram_id


async def get_user_from_internal(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
) -> User:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
