import asyncio

from aiogram import Bot

from app.bot_handlers import (
    BOT_COMMANDS,
    WEB_APP_COMMANDS,
    build_dispatcher,
    build_start_text,
    build_web_app_keyboard,
    configure_bot_commands,
    configure_menu_button,
)
from app.config import get_settings


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Add it to .env")

    bot = Bot(settings.bot_token)
    dp = build_dispatcher(settings)
    await configure_bot_commands(bot)
    await configure_menu_button(bot, settings)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
