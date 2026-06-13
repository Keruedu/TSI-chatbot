# Telegram Wear Reminder Bot

FastAPI bot for Vercel that reminds a Telegram chat on official wear-shirt days at 00:00 and 08:00 Vietnam time.

## Formula

For any date, find the Monday of that week, then:

```text
wear_offset = (monday.year + monday.month + monday.day) % 5
wear_date = monday + wear_offset days
```

Mapping: `0=Monday`, `1=Tuesday`, `2=Wednesday`, `3=Thursday`, `4=Friday`.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pytest
```

Run the API locally:

```powershell
.venv\Scripts\uvicorn app.main:app --reload
```

Optional local env file:

```text
TELEGRAM_BOT_TOKEN=123:abc
TELEGRAM_CHAT_ID=123456789
ALLOWED_CHAT_ID=123456789
CRON_SECRET=local-cron-secret
TELEGRAM_WEBHOOK_SECRET=local-webhook-secret
```

## Local validation

Check cron behavior without sending Telegram by omitting Telegram env vars:

```powershell
curl.exe -H "Authorization: Bearer local-cron-secret" "http://127.0.0.1:8000/api/cron/wear-reminder?date=2026-01-07"
curl.exe -H "Authorization: Bearer local-cron-secret" "http://127.0.0.1:8000/api/cron/wear-reminder?date=2026-01-08"
```

With Telegram env vars set, the first command sends a real message because `2026-01-07` is a wear day. The second returns `notificationSent=false`.

## Vercel env vars

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `ALLOWED_CHAT_ID`
- `CRON_SECRET`
- `TELEGRAM_WEBHOOK_SECRET`

`ALLOWED_CHAT_ID` is optional but recommended. If it is missing, the bot falls back to `TELEGRAM_CHAT_ID` for webhook command authorization.

## Telegram webhook

After deploy, point Telegram to:

```text
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://<your-domain>/api/telegram/webhook&secret_token=<TELEGRAM_WEBHOOK_SECRET>
```

Supported commands:

- `/today`
- `/next`
- `/schedule`
- `/test`

Suggested BotFather command list:

```text
today - Kiểm tra hôm nay có phải ngày mặc áo không
next - Xem ngày mặc áo tiếp theo
schedule - Xem lịch mặc áo tháng hiện tại
test - Gửi tin nhắn test production
```
