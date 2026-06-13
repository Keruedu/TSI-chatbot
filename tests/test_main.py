from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


client = TestClient(app)


def clear_settings_cache():
    get_settings.cache_clear()


def test_cron_rejects_missing_secret(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "secret")
    clear_settings_cache()

    response = client.get("/api/cron/wear-reminder?date=2026-01-07")

    assert response.status_code == 401


def test_cron_does_not_send_on_non_wear_day(monkeypatch, mocker):
    monkeypatch.setenv("CRON_SECRET", "secret")
    clear_settings_cache()
    send_message = mocker.patch("app.main.send_message")

    response = client.get(
        "/api/cron/wear-reminder?date=2026-01-08",
        headers={"Authorization": "Bearer secret"},
    )

    assert response.status_code == 200
    assert response.json()["isWearDay"] is False
    assert response.json()["notificationSent"] is False
    send_message.assert_not_called()


def test_cron_sends_on_wear_day(monkeypatch, mocker):
    monkeypatch.setenv("CRON_SECRET", "secret")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100")
    clear_settings_cache()
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


def test_webhook_rejects_missing_secret(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "hook-secret")
    clear_settings_cache()

    response = client.post("/api/telegram/webhook", json={})

    assert response.status_code == 401


def test_webhook_today_command_replies(monkeypatch, mocker):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "hook-secret")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    clear_settings_cache()
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
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "hook-secret")
    clear_settings_cache()
    send_message = mocker.patch("app.main.send_message")

    response = client.post(
        "/api/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "hook-secret"},
        json={"message": {"chat": {"id": -100}, "text": "/start"}},
    )

    assert response.status_code == 200
    assert response.json()["handled"] is False
    send_message.assert_not_called()
