import httpx

from app.config import settings


class BackendClient:
    def __init__(self) -> None:
        self.base = settings.backend_url.rstrip("/")
        self.secret = settings.internal_api_secret

    def _headers(self, telegram_id: int | None = None) -> dict:
        headers = {"X-Internal-Secret": self.secret}
        if telegram_id is not None:
            headers["X-Telegram-User-Id"] = str(telegram_id)
        return headers

    async def get_user(self, telegram_id: int) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{self.base}/api/internal/user/{telegram_id}",
                headers=self._headers(telegram_id),
            )
            r.raise_for_status()
            return r.json()

    async def get_status(self, telegram_id: int) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{self.base}/api/user/status",
                headers=self._headers(telegram_id),
            )
            r.raise_for_status()
            return r.json()

    async def set_language(self, telegram_id: int, language: str) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{self.base}/api/user/language",
                headers=self._headers(telegram_id),
                json={"language": language},
            )
            r.raise_for_status()
            return r.json()

    async def check_subscription(self, telegram_id: int) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{self.base}/api/user/check-subscription",
                headers=self._headers(telegram_id),
            )
            r.raise_for_status()
            return r.json()

    async def analyze(self, telegram_id: int, photo_bytes: bytes, filename: str) -> dict:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{self.base}/api/user/analyze",
                headers=self._headers(telegram_id),
                files={"screenshot": (filename, photo_bytes, "image/jpeg")},
            )
            r.raise_for_status()
            return r.json()

    async def get_settings(self) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{self.base}/api/internal/settings",
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    async def get_translations(self, locale: str) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{self.base}/api/internal/translations/{locale}",
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    async def admin_stats(self, telegram_id: int) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{self.base}/api/admin/stats",
                headers=self._headers(telegram_id),
            )
            r.raise_for_status()
            return r.json()

    async def admin_postback_urls(self, telegram_id: int) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{self.base}/api/admin/postback-urls",
                headers=self._headers(telegram_id),
            )
            r.raise_for_status()
            return r.json()

    async def grant_unlimited(self, telegram_id: int, target_id: int) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{self.base}/api/admin/unlimited/grant",
                headers=self._headers(telegram_id),
                json={"telegram_id": target_id},
            )
            r.raise_for_status()
            return r.json()

    async def create_unlimited_payment(self, telegram_id: int) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{self.base}/api/payments/unlimited/create",
                headers=self._headers(telegram_id),
            )
            r.raise_for_status()
            return r.json()
