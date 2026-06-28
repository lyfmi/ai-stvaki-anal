from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = ""
    public_base_url: str = "https://tgbot.snapink.ru"
    backend_url: str = "http://backend:8000"
    internal_api_secret: str = "change-me-internal-secret"
    admin_telegram_ids: str = "7649494487"
    webhook_path: str = "/telegram/webhook"
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8080

    @property
    def admin_ids(self) -> set[int]:
        return {int(x.strip()) for x in self.admin_telegram_ids.split(",") if x.strip()}


settings = BotSettings()
