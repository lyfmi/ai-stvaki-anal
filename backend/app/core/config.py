from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = ""
    webapp_url: str = "https://tgbot.snapink.ru"
    public_base_url: str = "https://tgbot.snapink.ru"
    admin_telegram_ids: str = "7649494487"
    internal_api_secret: str = "change-me-internal-secret"

    database_url: str = "postgresql+asyncpg://ai_bot:change-me-postgres@postgres:5432/ai_bet_bot"
    redis_url: str = "redis://redis:6379/0"

    groq_api_key: str = ""
    groq_api_base: str = "https://api.groq.com/openai/v1"
    groq_default_model: str = "llama-3.3-70b-versatile"
    groq_vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    groq_max_tokens: int = 1024
    ai_mock: bool = False
    ai_pipeline_version: str = "v4-groq"

    search_provider: str = "searxng"
    search_max_queries: int = 6
    search_max_results: int = 8
    search_cache_ttl_seconds: int = 7200
    searxng_base_url: str = "http://searxng:8080"

    tribute_api_key: str = ""
    tribute_shop_id: str = ""
    tribute_webhook_secret: str = ""

    reports_chat_id: str = ""

    daily_attempts_limit: int = 100
    storage_path: str = "/app/storage"

    @property
    def admin_ids(self) -> set[int]:
        return {int(x.strip()) for x in self.admin_telegram_ids.split(",") if x.strip()}


settings = Settings()
