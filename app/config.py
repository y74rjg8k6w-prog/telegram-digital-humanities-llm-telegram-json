from functools import lru_cache
import hashlib

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = ""
    web_app_url: str = "http://localhost:8000"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_table: str = "analyses"
    telegram_webhook_secret: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def effective_telegram_webhook_secret(self) -> str:
        """Stable webhook path secret.

        Production deploys should set TELEGRAM_WEBHOOK_SECRET explicitly. For tiny
        one-bot deployments this fallback keeps the webhook usable when only
        BOT_TOKEN is configured on the host: the secret is derived from the token
        and is never committed to the repository.
        """
        if self.telegram_webhook_secret:
            return self.telegram_webhook_secret
        if not self.bot_token:
            return ""
        return hashlib.sha256(f"telegram-webhook:{self.bot_token}".encode()).hexdigest()[:32]


@lru_cache
def get_settings() -> Settings:
    return Settings()
