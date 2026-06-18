import re
from html import unescape

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_RE = re.compile(r"@\w+")
SPACE_RE = re.compile(r"\s+")
NON_WORD_RE = re.compile(r"[^\w\sа-яА-ЯёЁ-]", re.UNICODE)


def normalize_text(value: object) -> str:
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
        value = "".join(parts)
    elif not isinstance(value, str):
        value = ""

    text = unescape(value)
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = NON_WORD_RE.sub(" ", text)
    return SPACE_RE.sub(" ", text).strip().lower()


def has_question(value: str) -> bool:
    return "?" in value or any(token in value.lower() for token in ("как ", "что ", "почему ", "зачем ", "когда "))
