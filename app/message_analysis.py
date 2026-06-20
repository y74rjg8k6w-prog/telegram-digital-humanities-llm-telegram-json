from __future__ import annotations

import re
from collections import Counter

_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+", re.UNICODE)
_POSITIVE = {"спасибо", "класс", "супер", "люблю", "ура", "отлично", "хорошо", "да", "давай", "рад", "рада"}
_NEGATIVE = {"нет", "плохо", "устал", "устала", "бесит", "страшно", "грустно", "злюсь", "проблема", "сложно"}
_QUESTION_WORDS = {"как", "что", "почему", "зачем", "когда", "где", "куда", "кто", "можно", "нужно"}


def analyze_single_message(text: str) -> dict:
    """Return a small, explainable analytic card for one Telegram message."""
    normalized = " ".join(text.strip().split())
    words = [word.lower() for word in _WORD_RE.findall(normalized)]
    word_count = len(words)
    char_count = len(normalized)
    unique_words = len(set(words))
    lexical_diversity = round(unique_words / word_count, 2) if word_count else 0
    questions = normalized.count("?") + sum(1 for word in words if word in _QUESTION_WORDS)
    exclamations = normalized.count("!")
    emoji_count = sum(1 for char in normalized if ord(char) > 10000)
    positive_hits = sum(1 for word in words if word in _POSITIVE)
    negative_hits = sum(1 for word in words if word in _NEGATIVE)

    if word_count == 0:
        tone = "пустое сообщение"
    elif positive_hits > negative_hits:
        tone = "скорее тёплый/позитивный"
    elif negative_hits > positive_hits:
        tone = "скорее напряжённый/негативный"
    elif questions:
        tone = "вопросительный/инициирующий"
    else:
        tone = "нейтральный"

    intent = _guess_intent(normalized, words, questions)
    keywords = [word for word, _ in Counter(w for w in words if len(w) >= 4).most_common(6)]
    summary = _summary(normalized, word_count, questions, exclamations, emoji_count, tone, intent, keywords)

    return {
        "text": normalized,
        "metrics": {
            "chars": char_count,
            "words": word_count,
            "unique_words": unique_words,
            "lexical_diversity": lexical_diversity,
            "questions": questions,
            "exclamations": exclamations,
            "emoji_count": emoji_count,
        },
        "tone": tone,
        "intent": intent,
        "keywords": keywords,
        "summary": summary,
    }


def format_single_message_report(text: str) -> str:
    analysis = analyze_single_message(text)
    metrics = analysis["metrics"]
    keywords = ", ".join(analysis["keywords"]) or "нет ярких ключевых слов"
    return (
        "Мини-анализ сообщения:\n"
        f"• Слов: {metrics['words']}, символов: {metrics['chars']}\n"
        f"• Вопросность: {metrics['questions']}, эмоц. знаки: {metrics['exclamations']}, эмодзи: {metrics['emoji_count']}\n"
        f"• Тон: {analysis['tone']}\n"
        f"• Намерение: {analysis['intent']}\n"
        f"• Ключевые слова: {keywords}\n\n"
        f"Вывод: {analysis['summary']}"
    )


def _guess_intent(text: str, words: list[str], questions: int) -> str:
    lower = text.lower()
    if questions:
        return "получить ответ или продолжить диалог"
    if any(word in words for word in ("спасибо", "благодарю")):
        return "выразить благодарность"
    if any(word in words for word in ("давай", "пойдём", "го", "встретимся", "созвонимся")):
        return "предложить действие"
    if any(marker in lower for marker in ("не могу", "не получится", "занят", "занята")):
        return "обозначить ограничение"
    if len(words) <= 3:
        return "короткая реакция"
    return "сообщить мысль или контекст"


def _summary(text: str, word_count: int, questions: int, exclamations: int, emoji_count: int, tone: str, intent: str, keywords: list[str]) -> str:
    if not text:
        return "Сообщение пустое, поэтому содержательная аналитика невозможна."
    parts = [f"Сообщение выглядит как {intent}; общий тон — {tone}."]
    if word_count <= 4:
        parts.append("Формат очень короткий, поэтому вывод осторожный: это скорее реакция, чем развернутая позиция.")
    elif word_count >= 25:
        parts.append("Текст достаточно развёрнутый: можно смотреть не только тон, но и структуру аргументации.")
    if questions:
        parts.append("Есть явный запрос к собеседнику, значит сообщение поддерживает продолжение диалога.")
    if exclamations or emoji_count:
        parts.append("Эмоциональная маркировка выше нейтральной за счёт знаков/эмодзи.")
    if keywords:
        parts.append("Смысловые опоры: " + ", ".join(keywords[:4]) + ".")
    return " ".join(parts)
