from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from aiogram import Bot
from aiogram.types import Update
from pydantic import BaseModel

from app.analyzer.pipeline import analyze_telegram_export
from app.bot_handlers import build_dispatcher
from app.config import get_settings
from app.llm import build_llm_summary
from app.message_analysis import analyze_pasted_messages, analyze_single_message, should_analyze_as_pasted_messages
from app.storage import save_analysis_result

app = FastAPI(title="Telegram Friendship Analyzer Web App")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


class MessageAnalysisRequest(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Загрузите Telegram result.json")

    raw = await file.read()
    if len(raw) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Файл больше 50 МБ")

    try:
        result = analyze_telegram_export(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result["llm_summary"] = await build_llm_summary(result)
    result["storage"] = await save_analysis_result("telegram_export", file.filename, result)
    return result


@app.post("/api/analyze-message")
async def analyze_message(payload: MessageAnalysisRequest) -> dict:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Введите хотя бы одно сообщение")
    if len(payload.text) > 12000:
        raise HTTPException(status_code=413, detail="Вставка длиннее 12000 символов")
    if should_analyze_as_pasted_messages(payload.text):
        result = analyze_pasted_messages(payload.text)
    else:
        result = analyze_single_message(payload.text)
    result["storage"] = await save_analysis_result("pasted_message", payload.text, result)
    return result


@app.post("/api/telegram-webhook/{secret}")
async def telegram_webhook(secret: str, request: Request) -> dict[str, bool]:
    settings = get_settings()
    if not settings.bot_token:
        raise HTTPException(status_code=503, detail="BOT_TOKEN is not configured")
    if not settings.telegram_webhook_secret or secret != settings.telegram_webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    update_data = await request.json()
    bot = Bot(settings.bot_token)
    dispatcher = build_dispatcher(settings)
    update = Update.model_validate(update_data, context={"bot": bot})
    try:
        await dispatcher.feed_update(bot, update)
    finally:
        await bot.session.close()
    return {"ok": True}
