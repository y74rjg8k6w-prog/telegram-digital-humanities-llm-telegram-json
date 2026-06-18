from __future__ import annotations

import asyncio
import json

from openai import OpenAI

from app.config import get_settings


async def build_llm_summary(analysis: dict) -> dict:
    settings = get_settings()
    if not settings.deepseek_api_key:
        return {
            "enabled": False,
            "text": local_summary(analysis),
        }

    prompt_payload = {
        "metrics": analysis["metrics"],
        "topics": analysis["topics"],
        "network": analysis["network"],
    }

    def call_llm() -> str:
        client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
        response = client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты аналитик digital humanities. Пиши по-русски. "
                        "Не ставь психологические диагнозы и не утверждай скрытые мотивы. "
                        "Интерпретируй только наблюдаемые признаки переписки."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Составь краткий аналитический портрет общения по агрегированным данным. "
                        "Структура: 1) ритм, 2) взаимность, 3) темы, 4) осторожный вывод. "
                        f"Данные JSON:\n{json.dumps(prompt_payload, ensure_ascii=False)[:12000]}"
                    ),
                },
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    try:
        text = await asyncio.to_thread(call_llm)
        return {"enabled": True, "text": text}
    except Exception as exc:
        return {
            "enabled": False,
            "text": local_summary(analysis),
            "error": f"LLM недоступна: {exc}",
        }


def local_summary(analysis: dict) -> str:
    metrics = analysis["metrics"]
    topics = analysis["topics"]
    words = ", ".join(word for word, _ in topics["top_words"][:8]) or "нет данных"
    return (
        f"В переписке найдено {metrics['total_messages']} сообщений за {metrics['days']} дн. "
        f"Индекс наблюдаемой близости переписки: {metrics['closeness_index']}/100. "
        f"Коэффициент взаимности: {metrics['reciprocity_score']}. "
        f"Главные слова: {words}. "
        "Это не психологический диагноз, а описание видимых паттернов общения."
    )
