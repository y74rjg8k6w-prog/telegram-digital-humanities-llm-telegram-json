from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.analyzer.pipeline import analyze_telegram_export
from app.llm import build_llm_summary
from app.message_analysis import analyze_single_message

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
    return result


@app.post("/api/analyze-message")
async def analyze_message(payload: MessageAnalysisRequest) -> dict:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Введите хотя бы одно сообщение")
    if len(payload.text) > 4000:
        raise HTTPException(status_code=413, detail="Сообщение длиннее 4000 символов")
    return analyze_single_message(payload.text)
