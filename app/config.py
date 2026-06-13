import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv(".env.local")


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    cron_secret: str | None
    telegram_webhook_secret: str | None


@lru_cache
def get_settings() -> Settings:
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        cron_secret=os.getenv("CRON_SECRET"),
        telegram_webhook_secret=os.getenv("TELEGRAM_WEBHOOK_SECRET"),
    )
