from __future__ import annotations

import json
import sys
from urllib.parse import urljoin
from urllib.request import urlopen
from urllib.parse import urlencode

from app.config import get_settings


def call_telegram(method: str, **params: str) -> dict:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty")
    body = urlencode(params).encode()
    with urlopen(f"https://api.telegram.org/bot{settings.bot_token}/{method}", data=body, timeout=20) as response:
        return json.loads(response.read().decode())


def main() -> int:
    settings = get_settings()
    if not settings.web_app_url.startswith("https://"):
        raise RuntimeError("WEB_APP_URL must be a public HTTPS URL before setting a webhook")
    if not settings.effective_telegram_webhook_secret:
        raise RuntimeError("BOT_TOKEN or TELEGRAM_WEBHOOK_SECRET is required")

    webhook_url = urljoin(settings.web_app_url.rstrip("/") + "/", f"api/telegram-webhook/{settings.effective_telegram_webhook_secret}")
    result = call_telegram(
        "setWebhook",
        url=webhook_url,
        allowed_updates=json.dumps(["message"]),
        drop_pending_updates="false",
    )
    safe = {"ok": result.get("ok"), "description": result.get("description"), "webhook_host": settings.web_app_url}
    print(json.dumps(safe, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
