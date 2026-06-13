from typing import Any

import httpx


class TelegramConfigError(RuntimeError):
    pass


async def send_message(bot_token: str | None, chat_id: str | int | None, text: str) -> dict[str, Any]:
    if not bot_token:
        raise TelegramConfigError("Missing TELEGRAM_BOT_TOKEN.")
    if chat_id is None or chat_id == "":
        raise TelegramConfigError("Missing TELEGRAM_CHAT_ID.")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def extract_command(update: dict[str, Any]) -> tuple[str | None, int | str | None]:
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    text = (message.get("text") or "").strip()

    if not text.startswith("/"):
        return None, chat.get("id")

    command = text.split(maxsplit=1)[0].split("@", maxsplit=1)[0].lower()
    return command, chat.get("id")
