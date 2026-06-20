from app.bot import BOT_COMMANDS, WEB_APP_COMMANDS, build_start_text, build_web_app_keyboard
from app.config import Settings
from app.message_analysis import analyze_pasted_messages, format_pasted_messages_report, format_single_message_report


def test_start_keyboard_contains_telegram_web_app_button() -> None:
    settings = Settings(bot_token="123:token", web_app_url="https://example.com/app")

    keyboard = build_web_app_keyboard(settings)
    button = keyboard.inline_keyboard[0][0]

    assert button.text == "Открыть анализатор"
    assert button.web_app is not None
    assert button.web_app.url == "https://example.com/app"


def test_start_text_explains_telegram_json_upload() -> None:
    text = build_start_text()

    assert "Telegram Web App" in text
    assert "одно любое сообщение" in text
    assert "result.json" in text
    assert "не публикуется" in text


def test_text_message_report_contains_minianalysis() -> None:
    report = format_single_message_report("Привет! Как ты? Давай созвонимся вечером 😊")

    assert "Мини-анализ сообщения" in report
    assert "Тон:" in report
    assert "Намерение:" in report


def test_pasted_messages_report_contains_emotion_abuse_and_red_flags() -> None:
    pasted = """
    Анна: Ты опять всё испортила!!! Нельзя тебе доверять.
    Я: Мне страшно и обидно, почему ты так говоришь?
    Анна: Если уйдёшь, я всем расскажу твои секреты.
    """

    report = format_pasted_messages_report(pasted)

    assert "Анализ вставленной переписки" in report
    assert "Сообщений: 3" in report
    assert "Эмоциональная шкала" in report
    assert "Абьюз/давление" in report
    assert "Красные флаги" in report
    assert "Анна" in report


def test_pasted_messages_detects_speaker_and_abuse_red_flags() -> None:
    pasted = """
    Анна: Ты опять всё испортила!!! Нельзя тебе доверять.
    Я: Мне страшно и обидно, почему ты так говоришь?
    Анна: Если уйдёшь, я всем расскажу твои секреты.
    """

    analysis = analyze_pasted_messages(pasted)

    assert analysis["message_count"] == 3
    assert analysis["participants"]["Анна"]["messages"] == 2
    assert analysis["emotion_scale"]["anger"] >= 60
    assert analysis["emotion_scale"]["fear"] >= 30
    assert analysis["abuse"]["score"] >= 50
    assert any(flag["type"] == "threat" for flag in analysis["red_flags"])
    assert any(flag["type"] == "blame_or_devaluation" for flag in analysis["red_flags"])


def test_pasted_messages_measure_friendship_high_for_warm_balanced_chat() -> None:
    pasted = """
    Маша: Спасибо, что поддержала меня сегодня ❤️
    Я: Я тоже очень рада, люблю наши разговоры.
    Маша: Давай завтра погуляем и всё спокойно обсудим?
    Я: Да, давай, обнимаю тебя.
    """

    analysis = analyze_pasted_messages(pasted)

    assert analysis["friendship"]["score"] >= 75
    assert analysis["friendship"]["level"] == "крепкая"
    assert analysis["friendship"]["reciprocity"] >= 80
    assert analysis["friendship"]["warmth"] >= 70
    assert analysis["friendship"]["risk_penalty"] == 0


def test_pasted_messages_report_contains_friendship_meter() -> None:
    pasted = """
    Маша: Спасибо за помощь, ты супер.
    Я: Рада поддержать, давай увидимся завтра.
    """

    report = format_pasted_messages_report(pasted)

    assert "Дружба/поддержка" in report
    assert "Взаимность" in report


def test_bot_menu_commands_include_pic_shortcut() -> None:
    commands = {command.command: command.description for command in BOT_COMMANDS}

    assert "start" in commands
    assert "pic" in WEB_APP_COMMANDS
    assert commands["pic"] == "Открыть мини-приложение анализатора"
    assert "webapp" in commands

