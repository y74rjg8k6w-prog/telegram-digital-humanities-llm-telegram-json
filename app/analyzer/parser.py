import json
from datetime import datetime
from typing import Any

import pandas as pd

from app.analyzer.cleaning import has_question, normalize_text


def parse_telegram_export(raw: bytes) -> pd.DataFrame:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        payload = json.loads(raw.decode("utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError("Файл не похож на валидный Telegram JSON") from exc

    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ValueError("В JSON не найден массив messages")

    rows: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict) or message.get("type") != "message":
            continue

        raw_text = message.get("text", "")
        clean_text = normalize_text(raw_text)
        if not clean_text:
            continue

        sender = str(message.get("from") or message.get("actor") or "Unknown")
        date_raw = message.get("date")
        try:
            date = pd.to_datetime(date_raw)
        except Exception:
            date = pd.NaT

        rows.append(
            {
                "id": message.get("id"),
                "sender": sender,
                "date": date,
                "text": _text_to_plain(raw_text),
                "clean_text": clean_text,
                "reply_to_id": message.get("reply_to_message_id"),
                "text_len": len(clean_text),
                "word_count": len(clean_text.split()),
                "has_question": has_question(_text_to_plain(raw_text)),
            }
        )

    if not rows:
        raise ValueError("Не нашлось текстовых сообщений для анализа")

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if df.empty:
        raise ValueError("В сообщениях нет корректных дат")
    return df


def _text_to_plain(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return ""
