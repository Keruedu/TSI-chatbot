from datetime import date

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


client = TestClient(app)
BOT_ENVS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "ALLOWED_CHAT_ID",
    "CRON_SECRET",
    "TELEGRAM_WEBHOOK_SECRET",
]


def clear_settings_cache(monkeypatch):
    for env_name in BOT_ENVS:
        monkeypatch.delenv(env_name, raising=False)
    get_settings.cache_clear()


def test_cron_rejects_missing_secret(monkeypatch):
    clear_settings_cache(monkeypatch)
    monkeypatch.setenv("CRON_SECRET", "secret")
    get_settings.cache_clear()

    response = client.get("/api/cron/wear-reminder?date=2026-01-07")

    assert response.status_code == 401


def test_cron_does_not_send_on_non_wear_day(monkeypatch, mocker, capsys):
    clear_settings_cache(monkeypatch)
    monkeypatch.setenv("CRON_SECRET", "secret")
    get_settings.cache_clear()
    send_message = mocker.patch("app.main.send_message")

    response = client.get(
        "/api/cron/wear-reminder?date=2026-01-08",
        headers={"Authorization": "Bearer secret"},
    )

    assert response.status_code == 200
    assert response.json()["isWearDay"] is False
    assert response.json()["notificationSent"] is False
    send_message.assert_not_called()
    log_output = capsys.readouterr().out
    assert '"event": "wear_reminder_cron"' in log_output
    assert '"localDate": "2026-01-08"' in log_output
    assert '"isWearDay": false' in log_output
    assert '"notificationSent": false' in log_output


def test_cron_sends_on_wear_day(monkeypatch, mocker, capsys):
    clear_settings_cache(monkeypatch)
    monkeypatch.setenv("CRON_SECRET", "secret")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100")
    get_settings.cache_clear()
    send_message = mocker.patch("app.main.send_message", return_value={"ok": True})

    response = client.get(
        "/api/cron/wear-reminder?date=2026-01-07",
        headers={"Authorization": "Bearer secret"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["isWearDay"] is True
    assert body["notificationSent"] is True
    send_message.assert_called_once()
    log_output = capsys.readouterr().out
    assert '"event": "wear_reminder_cron"' in log_output
    assert '"localDate": "2026-01-07"' in log_output
    assert '"isWearDay": true' in log_output
    assert '"notificationSent": true' in log_output
    assert '"triggeredByTestDate": true' in log_output


def test_webhook_rejects_missing_secret(monkeypatch):
    clear_settings_cache(monkeypatch)
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "hook-secret")
    get_settings.cache_clear()

    response = client.post("/api/telegram/webhook", json={})

    assert response.status_code == 401


def test_webhook_today_command_replies(monkeypatch, mocker):
    clear_settings_cache(monkeypatch)
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "hook-secret")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    get_settings.cache_clear()
    send_message = mocker.patch("app.main.send_message", return_value={"ok": True})

    response = client.post(
        "/api/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "hook-secret"},
        json={"message": {"chat": {"id": -100}, "text": "/today"}},
    )

    assert response.status_code == 200
    assert response.json()["handled"] is True
    send_message.assert_called_once()


def test_webhook_ignores_unknown_command(monkeypatch, mocker):
    clear_settings_cache(monkeypatch)
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "hook-secret")
    get_settings.cache_clear()
    send_message = mocker.patch("app.main.send_message")

    response = client.post(
        "/api/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "hook-secret"},
        json={"message": {"chat": {"id": -100}, "text": "/start"}},
    )

    assert response.status_code == 200
    assert response.json()["handled"] is False
    send_message.assert_not_called()


def test_webhook_schedule_command_replies_with_current_month(monkeypatch, mocker):
    clear_settings_cache(monkeypatch)
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "hook-secret")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123")
    get_settings.cache_clear()
    mocker.patch("app.main.today_vietnam", return_value=date(2026, 1, 8))
    send_message = mocker.patch("app.main.send_message", return_value={"ok": True})

    response = client.post(
        "/api/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "hook-secret"},
        json={"message": {"chat": {"id": 123}, "text": "/schedule"}},
    )

    assert response.status_code == 200
    assert response.json()["handled"] is True
    send_message.assert_called_once_with(
        "token",
        123,
        "Lịch mặc áo tháng 01/2026\n"
        "- 07/01 (thứ 4)\n"
        "- 16/01 (thứ 6)\n"
        "- 20/01 (thứ 3)\n"
        "- 29/01 (thứ 5)",
    )


def test_webhook_test_command_replies_when_chat_allowed(monkeypatch, mocker):
    clear_settings_cache(monkeypatch)
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "hook-secret")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123")
    get_settings.cache_clear()
    send_message = mocker.patch("app.main.send_message", return_value={"ok": True})

    response = client.post(
        "/api/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "hook-secret"},
        json={"message": {"chat": {"id": 123}, "text": "/test"}},
    )

    assert response.status_code == 200
    assert response.json()["handled"] is True
    send_message.assert_called_once_with(
        "token",
        123,
        "Test bot thành công\nBot đã gửi được tin nhắn production.",
    )


def test_webhook_uses_telegram_chat_id_as_allowed_chat_fallback(monkeypatch, mocker):
    clear_settings_cache(monkeypatch)
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "hook-secret")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    get_settings.cache_clear()
    send_message = mocker.patch("app.main.send_message", return_value={"ok": True})

    response = client.post(
        "/api/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "hook-secret"},
        json={"message": {"chat": {"id": 123}, "text": "/test"}},
    )

    assert response.status_code == 200
    assert response.json()["handled"] is True
    send_message.assert_called_once()


def test_webhook_does_not_reply_when_chat_is_not_allowed(monkeypatch, mocker):
    clear_settings_cache(monkeypatch)
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "hook-secret")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("ALLOWED_CHAT_ID", "123")
    get_settings.cache_clear()
    send_message = mocker.patch("app.main.send_message")

    for command in ["/today", "/next", "/schedule", "/test"]:
        response = client.post(
            "/api/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "hook-secret"},
            json={"message": {"chat": {"id": 999}, "text": command}},
        )

        assert response.status_code == 200
        assert response.json()["handled"] is False
        assert response.json()["reason"] == "chat_not_allowed"

    send_message.assert_not_called()
