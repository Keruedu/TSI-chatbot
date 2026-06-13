import json
from datetime import date

from fastapi import FastAPI, Header, HTTPException, Query, Request

from app.config import get_settings
from app.schedule import (
    build_month_schedule_message,
    build_next_status_message,
    build_test_message,
    build_today_status_message,
    build_wear_reminder_message,
    is_wear_day,
    parse_iso_date,
    today_vietnam,
)
from app.telegram import TelegramConfigError, extract_command, send_message


app = FastAPI(title="Telegram Wear Reminder Bot")


def resolve_target_date(raw_date: str | None) -> date:
    if raw_date is None:
        return today_vietnam()

    try:
        return parse_iso_date(raw_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="date must use YYYY-MM-DD format") from exc


def is_allowed_chat(chat_id: str | int | None, allowed_chat_id: str | None) -> bool:
    if not allowed_chat_id:
        return True
    if chat_id is None:
        return False
    return str(chat_id) == str(allowed_chat_id)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "telegram-wear-reminder-bot", "status": "ok"}


@app.get("/api/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/cron/wear-reminder")
async def wear_reminder(
    authorization: str | None = Header(default=None),
    raw_date: str | None = Query(default=None, alias="date"),
) -> dict[str, object]:
    settings = get_settings()
    if not settings.cron_secret or authorization != f"Bearer {settings.cron_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    target_date = resolve_target_date(raw_date)
    wear_day = is_wear_day(target_date)
    notification_sent = False
    telegram_result: dict[str, object] | None = None

    if wear_day:
        message = build_wear_reminder_message(target_date)
        try:
            telegram_result = await send_message(
                settings.telegram_bot_token,
                settings.telegram_chat_id,
                message,
            )
            notification_sent = True
        except TelegramConfigError:
            if raw_date is None:
                raise

    print(
        json.dumps(
            {
                "event": "wear_reminder_cron",
                "localDate": target_date.isoformat(),
                "isWearDay": wear_day,
                "notificationSent": notification_sent,
                "chatId": settings.telegram_chat_id,
                "triggeredByTestDate": raw_date is not None,
            },
            ensure_ascii=False,
        )
    )

    return {
        "ok": True,
        "localDate": target_date.isoformat(),
        "isWearDay": wear_day,
        "notificationSent": notification_sent,
        "telegramResult": telegram_result,
    }


@app.post("/api/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, object]:
    settings = get_settings()
    if (
        not settings.telegram_webhook_secret
        or x_telegram_bot_api_secret_token != settings.telegram_webhook_secret
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    update = await request.json()
    command, chat_id = extract_command(update)
    target_date = today_vietnam()

    if not is_allowed_chat(chat_id, settings.allowed_chat_id):
        return {
            "ok": True,
            "handled": False,
            "command": command,
            "reason": "chat_not_allowed",
        }

    if command == "/today":
        await send_message(settings.telegram_bot_token, chat_id, build_today_status_message(target_date))
        return {"ok": True, "handled": True, "command": command}

    if command == "/next":
        await send_message(settings.telegram_bot_token, chat_id, build_next_status_message(target_date))
        return {"ok": True, "handled": True, "command": command}

    if command == "/schedule":
        await send_message(settings.telegram_bot_token, chat_id, build_month_schedule_message(target_date))
        return {"ok": True, "handled": True, "command": command}

    if command == "/test":
        await send_message(settings.telegram_bot_token, chat_id, build_test_message())
        return {"ok": True, "handled": True, "command": command}

    return {"ok": True, "handled": False, "command": command}
