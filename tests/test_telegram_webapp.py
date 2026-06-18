from app.bot import WEB_APP_COMMANDS, build_start_text, build_web_app_keyboard
from app.config import Settings


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
    assert "result.json" in text
    assert "не публикуется" in text


def test_pic_command_is_registered_as_web_app_alias() -> None:
    assert "webapp" in WEB_APP_COMMANDS
    assert "pic" in WEB_APP_COMMANDS

