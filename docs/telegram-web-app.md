# Telegram Web App launch checklist

This project is already structured as a Telegram Web App:

- `app/main.py` serves the FastAPI web interface.
- `app/templates/index.html` loads `https://telegram.org/js/telegram-web-app.js`.
- `app/static/app.js` calls `Telegram.WebApp.ready()` and `Telegram.WebApp.expand()`.
- `app/bot.py` sends an inline `web_app` button and, when `WEB_APP_URL` is public HTTPS, installs a Telegram menu button.

## Local smoke run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## Telegram run

Telegram Web Apps require a public HTTPS URL.

1. Start the app locally:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. Expose it with a tunnel or deploy it to a server:

   ```bash
   ngrok http 8000
   ```

3. Create `.env`:

   ```bash
   cp .env.example .env
   ```

4. Fill in:

   ```env
   BOT_TOKEN=123456:your_real_token
   WEB_APP_URL=https://your-public-https-url.example
   ```

5. Start the bot:

   ```bash
   python3 -m app.bot
   ```

6. In Telegram, send `/start` or `/webapp` to the bot and tap **Открыть анализатор**.

## Bot behavior

- `/start` explains what the app does and shows the Web App button.
- `/webapp` sends the Web App button directly.
- On startup, if `WEB_APP_URL` starts with `https://`, the bot registers a persistent menu button named **Анализатор**.

## Privacy note

Do not commit real Telegram exports. The repo includes only `data/example_result.json`, a synthetic example. Keep real `result.json` files local and ignored by Git.
