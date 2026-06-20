from app.bot import BOT_COMMANDS, WEB_APP_COMMANDS, build_start_text, build_web_app_keyboard
from app.config import Settings
from app.message_analysis import format_single_message_report


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


def test_bot_menu_commands_include_pic_shortcut() -> None:
    commands = {command.command: command.description for command in BOT_COMMANDS}

    assert "start" in commands
    assert "pic" in WEB_APP_COMMANDS
    assert commands["pic"] == "Открыть мини-приложение анализатора"
    assert "webapp" in commands

