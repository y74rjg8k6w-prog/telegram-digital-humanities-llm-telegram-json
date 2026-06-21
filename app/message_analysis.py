from __future__ import annotations

import re
from collections import Counter, defaultdict

_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+", re.UNICODE)
_SPEAKER_LINE_RE = re.compile(r"^\s*(?P<speaker>[^:\n]{1,40})\s*:\s*(?P<text>.+?)\s*$")
_POSITIVE = {"спасибо", "класс", "супер", "люблю", "ура", "отлично", "хорошо", "да", "давай", "рад", "рада"}
_NEGATIVE = {"нет", "плохо", "устал", "устала", "бесит", "страшно", "грустно", "злюсь", "проблема", "сложно"}
_QUESTION_WORDS = {"как", "что", "почему", "зачем", "когда", "где", "куда", "кто", "можно", "нужно"}

_EMOTION_LEXICON: dict[str, set[str]] = {
    "warmth": {"люблю", "спасибо", "скучаю", "милый", "милая", "обнимаю", "рада", "рад", "класс", "супер", "хорошо", "давай", "поддержала", "поддержал", "поддержать", "помогла", "помог", "помочь", "вместе", "обсудим"},
    "anger": {"бесит", "ненавижу", "злюсь", "достал", "достала", "идиот", "тупой", "тупая", "опять", "испортил", "испортила", "виноват", "виновата"},
    "fear": {"страшно", "боюсь", "угроза", "угрожаешь", "опасно", "уйдёшь", "уйдешь", "расскажу", "секреты", "шантаж"},
    "sadness": {"грустно", "обидно", "больно", "плачу", "одиноко", "жаль", "устала", "устал"},
    "control": {"нельзя", "должна", "должен", "запрещаю", "немедленно", "обязан", "обязана", "проверю", "отчитайся"},
    "anxiety": {"почему", "как", "когда", "можно", "нужно", "срочно", "переживаю", "волнусь", "волнуешься"},
}

_RED_FLAG_PATTERNS: list[tuple[str, str, tuple[str, ...]]] = [
    ("threat", "угроза / шантаж", ("если уйд", "я всем расскажу", "пожалеешь", "угрож", "шантаж", "секреты")),
    ("control", "контроль / запрет", ("нельзя тебе", "я запрещаю", "ты должна", "ты должен", "отчитайся", "проверю телефон", "немедленно")),
    ("blame_or_devaluation", "обесценивание / обвинение", ("ты опять", "всё испорт", "все испорт", "нельзя доверять", "ты виноват", "ты виновата", "идиот", "тупая", "тупой")),
    ("isolation", "изоляция", ("не общайся", "удали его", "удали её", "никому не говори", "только со мной")),
]


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
        "mode": "single_message",
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


def analyze_pasted_messages(text: str) -> dict:
    """Analyze several pasted chat messages without requiring Telegram JSON export.

    Supported paste styles:
    - `Анна: текст сообщения`
    - plain lines without speaker; they are grouped as `Сообщение N`
    """
    messages = _parse_pasted_messages(text)
    all_text = "\n".join(message["text"] for message in messages)
    words = [word.lower() for word in _WORD_RE.findall(all_text)]
    emotion_scale = _emotion_scale(words, all_text)
    red_flags = _red_flags(messages)
    abuse = _abuse_summary(emotion_scale, red_flags, messages)
    participants = _participant_stats(messages, red_flags)
    friendship = _friendship_summary(emotion_scale, abuse, messages)
    conversation_health = _conversation_health(messages, emotion_scale, abuse, friendship, red_flags)
    audience_segments = _audience_segments(messages, conversation_health, red_flags)
    keywords = [word for word, _ in Counter(w for w in words if len(w) >= 4).most_common(8)]

    return {
        "mode": "multi_message",
        "message_count": len(messages),
        "participants": participants,
        "emotion_scale": emotion_scale,
        "abuse": abuse,
        "friendship": friendship,
        "conversation_health": conversation_health,
        "audience_segments": audience_segments,
        "red_flags": red_flags,
        "keywords": keywords,
        "summary": _multi_summary(len(messages), emotion_scale, abuse, red_flags, friendship),
        "messages": messages,
    }


def should_analyze_as_pasted_messages(text: str) -> bool:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    speaker_lines = sum(1 for line in lines if _SPEAKER_LINE_RE.match(line))
    return len(lines) >= 3 or speaker_lines >= 2


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


def format_pasted_messages_report(text: str) -> str:
    analysis = analyze_pasted_messages(text)
    participants = analysis["participants"]
    emotion_scale = analysis["emotion_scale"]
    red_flags = analysis["red_flags"]
    abuse = analysis["abuse"]
    keywords = ", ".join(analysis["keywords"]) or "нет ярких ключевых слов"
    participant_lines = []
    for name, stats in sorted(participants.items(), key=lambda item: (-item[1]["messages"], item[0]))[:5]:
        participant_lines.append(
            f"• {name}: {stats['messages']} сообщ.; тон {stats['tone']}; красных флагов {stats['red_flags']}"
        )
    flag_lines = []
    for flag in red_flags[:5]:
        flag_lines.append(f"• {flag['label']}: {flag['speaker']} — «{flag['snippet']}»")
    if not flag_lines:
        flag_lines.append("• Явных красных флагов по эвристикам не найдено.")

    return (
        "Анализ вставленной переписки\n"
        f"Сообщений: {analysis['message_count']}\n\n"
        "Эмоциональная шкала:\n"
        f"• Тепло/симпатия: {_bar(emotion_scale['warmth'])} {emotion_scale['warmth']}%\n"
        f"• Злость/раздражение: {_bar(emotion_scale['anger'])} {emotion_scale['anger']}%\n"
        f"• Страх/тревога: {_bar(emotion_scale['fear'])} {emotion_scale['fear']}%\n"
        f"• Грусть/обида: {_bar(emotion_scale['sadness'])} {emotion_scale['sadness']}%\n"
        f"• Контроль/давление: {_bar(emotion_scale['control'])} {emotion_scale['control']}%\n\n"
        f"Дружба/поддержка: {analysis['friendship']['level']} ({analysis['friendship']['score']}%)\n"
        f"• Взаимность: {_bar(analysis['friendship']['reciprocity'])} {analysis['friendship']['reciprocity']}%\n"
        f"• Тёплые маркеры: {_bar(analysis['friendship']['warmth'])} {analysis['friendship']['warmth']}%\n"
        f"{analysis['friendship']['explanation']}\n\n"
        f"Абьюз/давление: {abuse['level']} ({abuse['score']}%)\n"
        f"{abuse['explanation']}\n\n"
        f"Здоровье диалога: {analysis['conversation_health']['level']} ({analysis['conversation_health']['score']}%)\n"
        f"• Баланс: {_bar(analysis['conversation_health']['balance'])} {analysis['conversation_health']['balance']}%\n"
        f"• Конфликтность: {_bar(analysis['conversation_health']['conflict'])} {analysis['conversation_health']['conflict']}%\n"
        f"• Срочность: {_bar(analysis['conversation_health']['urgency'])} {analysis['conversation_health']['urgency']}%\n"
        f"{analysis['conversation_health']['explanation']}\n\n"
        "Для кого полезно:\n"
        + "\n".join(f"• {segment}" for segment in analysis["audience_segments"][:4])
        + "\n\nОт кого что видно:\n"
        + "\n".join(participant_lines)
        + "\n\nКрасные флаги:\n"
        + "\n".join(flag_lines)
        + f"\n\nКлючевые слова: {keywords}\n\n"
        "Важно: это не диагноз и не юридическая оценка, а быстрый эвристический разбор текста. "
        "Если есть угрозы, страх за безопасность или принуждение — лучше обсудить это с живым специалистом/близким человеком."
    )


def format_message_report(text: str) -> str:
    if should_analyze_as_pasted_messages(text):
        return format_pasted_messages_report(text)
    return format_single_message_report(text)


def _parse_pasted_messages(text: str) -> list[dict]:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return []
    messages: list[dict] = []
    for index, line in enumerate(lines, start=1):
        match = _SPEAKER_LINE_RE.match(line)
        if match:
            speaker = match.group("speaker").strip()
            body = match.group("text").strip()
        else:
            speaker = f"Сообщение {index}"
            body = line
        messages.append({"speaker": speaker, "text": body})
    return messages


def _emotion_scale(words: list[str], text: str) -> dict[str, int]:
    lower = text.lower()
    scores: dict[str, int] = {}
    for emotion, lexicon in _EMOTION_LEXICON.items():
        hits = sum(1 for word in words if word in lexicon)
        phrase_boost = sum(1 for phrase in lexicon if " " in phrase and phrase in lower)
        raw = hits + phrase_boost
        score = min(100, raw * 28)
        scores[emotion] = score
    if "!" in text:
        scores["anger"] = min(100, scores["anger"] + min(25, text.count("!") * 7))
    if "?" in text:
        scores["anxiety"] = min(100, scores["anxiety"] + min(25, text.count("?") * 6))
    return scores


def _red_flags(messages: list[dict]) -> list[dict]:
    flags: list[dict] = []
    for message in messages:
        lower = message["text"].lower()
        for flag_type, label, patterns in _RED_FLAG_PATTERNS:
            for pattern in patterns:
                if pattern in lower:
                    flags.append(
                        {
                            "type": flag_type,
                            "label": label,
                            "speaker": message["speaker"],
                            "snippet": _shorten(message["text"]),
                            "match": pattern,
                        }
                    )
                    break
    return flags


def _abuse_summary(emotion_scale: dict[str, int], red_flags: list[dict], messages: list[dict]) -> dict:
    score = min(
        100,
        len(red_flags) * 22
        + emotion_scale.get("control", 0) // 2
        + emotion_scale.get("fear", 0) // 3
        + emotion_scale.get("anger", 0) // 4,
    )
    if score >= 65:
        level = "высокий"
    elif score >= 30:
        level = "средний"
    elif score > 0:
        level = "низкий"
    else:
        level = "не видно"
    if red_flags:
        explanation = f"Найдено {len(red_flags)} маркер(ов) давления/риска: угрозы, контроль, обвинение или обесценивание."
    elif messages:
        explanation = "Явных маркеров угроз, контроля или обесценивания не найдено, но контекст всё равно важен."
    else:
        explanation = "Нет сообщений для анализа."
    return {"score": score, "level": level, "explanation": explanation}


def _participant_stats(messages: list[dict], red_flags: list[dict]) -> dict:
    by_speaker: dict[str, dict] = defaultdict(lambda: {"messages": 0, "words": 0, "red_flags": 0, "tone": "нейтральный"})
    red_flag_counts = Counter(flag["speaker"] for flag in red_flags)
    for message in messages:
        speaker = message["speaker"]
        words = [word.lower() for word in _WORD_RE.findall(message["text"])]
        by_speaker[speaker]["messages"] += 1
        by_speaker[speaker]["words"] += len(words)
    for speaker, stats in by_speaker.items():
        stats["red_flags"] = red_flag_counts[speaker]
        if stats["red_flags"]:
            stats["tone"] = "давящий/рисковый"
        elif speaker.lower() in {"я", "me", "i"}:
            stats["tone"] = "своя позиция/реакция"
        else:
            stats["tone"] = "без явных рисков"
    return dict(by_speaker)


def _friendship_summary(emotion_scale: dict[str, int], abuse: dict, messages: list[dict]) -> dict:
    message_counts = Counter(message["speaker"] for message in messages)
    total_messages = sum(message_counts.values())
    if total_messages <= 0:
        return {
            "score": 0,
            "level": "неясная",
            "warmth": 0,
            "reciprocity": 0,
            "support": 0,
            "risk_penalty": 0,
            "explanation": "Недостаточно сообщений, чтобы оценить дружбу или поддержку.",
        }

    if len(message_counts) >= 2:
        shares = [count / total_messages for count in message_counts.values()]
        reciprocity = round((1 - (max(shares) - min(shares))) * 100)
    else:
        reciprocity = 35

    all_text = "\n".join(message["text"].lower() for message in messages)
    support_markers = (
        "спасибо",
        "поддерж",
        "помог",
        "помочь",
        "люблю",
        "обнимаю",
        "рада",
        "рад",
        "давай",
        "вместе",
        "обсудим",
        "супер",
    )
    support_hits = sum(all_text.count(marker) for marker in support_markers)
    support = min(100, support_hits * 20)
    warmth = max(emotion_scale.get("warmth", 0), support)
    risk_penalty = min(75, abuse.get("score", 0))
    score = round(max(0, min(100, warmth * 0.38 + reciprocity * 0.32 + support * 0.30 - risk_penalty)))

    if score >= 75:
        level = "крепкая"
    elif score >= 50:
        level = "тёплая, но неравномерная"
    elif score >= 25:
        level = "хрупкая"
    else:
        level = "напряжённая"

    if risk_penalty >= 30:
        explanation = "Поддержка может быть перекрыта давлением или красными флагами — дружбу стоит оценивать осторожно."
    elif score >= 75:
        explanation = "Поддержка выглядит взаимной: есть тёплые слова, отклик и желание продолжать контакт."
    elif support:
        explanation = "Поддержка есть, но по фрагменту она выглядит не полностью сбалансированной."
    else:
        explanation = "Явных маркеров поддержки мало; для оценки дружбы нужен больший фрагмент диалога."

    return {
        "score": score,
        "level": level,
        "warmth": warmth,
        "reciprocity": reciprocity,
        "support": support,
        "risk_penalty": risk_penalty,
        "explanation": explanation,
    }


def _conversation_health(messages: list[dict], emotion_scale: dict[str, int], abuse: dict, friendship: dict, red_flags: list[dict]) -> dict:
    message_counts = Counter(message["speaker"] for message in messages)
    total = sum(message_counts.values())
    if total <= 0:
        return {
            "score": 0,
            "level": "нет данных",
            "balance": 0,
            "conflict": 0,
            "urgency": 0,
            "explanation": "Недостаточно сообщений для оценки здоровья диалога.",
            "recommendations": ["Добавьте хотя бы несколько реплик с обеих сторон."],
        }

    if len(message_counts) >= 2:
        shares = [count / total for count in message_counts.values()]
        balance = round((1 - (max(shares) - min(shares))) * 100)
    else:
        balance = 25

    raw_text = "\n".join(message["text"] for message in messages)
    urgency = min(100, raw_text.count("!") * 8 + raw_text.count("?") * 4 + emotion_scale.get("anxiety", 0) // 2)
    conflict = min(
        100,
        abuse.get("score", 0) // 2
        + emotion_scale.get("anger", 0) // 2
        + emotion_scale.get("control", 0) // 3
        + len(red_flags) * 12,
    )
    score = round(max(0, min(100, balance * 0.35 + friendship.get("score", 0) * 0.45 + (100 - conflict) * 0.20 - urgency * 0.08)))
    if score >= 75:
        level = "устойчивое"
    elif score >= 50:
        level = "нормальное, но есть зоны внимания"
    elif score >= 25:
        level = "напряжённое"
    else:
        level = "кризисное/рисковое"

    recommendations: list[str] = []
    if balance < 45:
        recommendations.append("Проверить дисбаланс: один участник заметно доминирует или отвечает чаще другого.")
    if conflict >= 45:
        recommendations.append("Разобрать конфликтные фразы отдельно и не делать вывод по одному сообщению.")
    if urgency >= 45:
        recommendations.append("Снизить срочность: перевести диалог из реактивного режима в спокойный разговор.")
    if red_flags:
        recommendations.append("Красные флаги перепроверить вручную: угроза, контроль или обесценивание зависят от контекста.")
    if not recommendations:
        recommendations.append("Можно смотреть динамику на большем фрагменте: как меняются тепло, баланс и темы.")

    return {
        "score": score,
        "level": level,
        "balance": balance,
        "conflict": conflict,
        "urgency": urgency,
        "explanation": f"Индекс собран из баланса реплик, поддержки, конфликтности и срочности. Главная зона внимания: {recommendations[0]}",
        "recommendations": recommendations,
    }


def _audience_segments(messages: list[dict], conversation_health: dict, red_flags: list[dict]) -> list[str]:
    segments = [
        "Личные переписки: быстро понять тон, взаимность и где разговор начинает ломаться.",
        "Родители/подростки: увидеть давление, тревожность и безопасно обсудить сложные фразы.",
        "Комьюнити и чаты: отлавливать токсичность, эскалацию и перекос участия до конфликта.",
    ]
    if len({message["speaker"] for message in messages}) >= 3:
        segments.append("Групповые чаты: сравнить роли участников и кто чаще несёт риск/поддержку.")
    if red_flags:
        segments.append("Помогающие специалисты: получить список фрагментов, которые стоит проверить вручную.")
    elif conversation_health.get("score", 0) >= 70:
        segments.append("Создатели контента/HR: показывать здоровые примеры коммуникации и поддержки.")
    else:
        segments.append("Медиаторы: найти, что именно ухудшает баланс и срочность диалога.")
    return segments


def _multi_summary(message_count: int, emotion_scale: dict[str, int], abuse: dict, red_flags: list[dict], friendship: dict) -> str:
    dominant = max(emotion_scale.items(), key=lambda item: item[1])[0] if emotion_scale else "neutral"
    labels = {
        "warmth": "тепло/симпатия",
        "anger": "злость/раздражение",
        "fear": "страх/тревога",
        "sadness": "грусть/обида",
        "control": "контроль/давление",
        "anxiety": "тревожность/вопросительность",
    }
    if red_flags:
        return f"В {message_count} сообщениях доминирует {labels.get(dominant, dominant)}; уровень риска — {abuse['level']}; дружба/поддержка — {friendship['level']}. Есть красные флаги, их стоит проверить вручную по контексту."
    return f"В {message_count} сообщениях доминирует {labels.get(dominant, dominant)}; дружба/поддержка — {friendship['level']} ({friendship['score']}%); явные красные флаги не найдены."


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


def _bar(score: int) -> str:
    filled = min(10, max(0, round(score / 10)))
    return "█" * filled + "░" * (10 - filled)


def _shorten(text: str, limit: int = 80) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"
