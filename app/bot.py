import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, Message, WebAppInfo

from app.config import Settings, get_settings


WEB_APP_BUTTON_TEXT = "Открыть анализатор"
MENU_BUTTON_TEXT = "Анализатор"


def build_web_app_keyboard(settings: Settings) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=WEB_APP_BUTTON_TEXT,
                    web_app=WebAppInfo(url=settings.web_app_url),
                )
            ]
        ]
    )


def build_start_text() -> str:
    return (
        "Это Telegram Web App для анализа переписки.\n\n"
        "1. Экспортируй личный чат из Telegram Desktop в формате JSON.\n"
        "2. Открой анализатор кнопкой ниже.\n"
        "3. Загрузи result.json и получи метрики, графики, TF-IDF и осторожный LLM-портрет.\n\n"
        "Исходная переписка не публикуется в GitHub; в репозитории лежит только синтетический пример."
    )


def is_public_https_url(url: str) -> bool:
    return url.startswith("https://")


async def configure_menu_button(bot: Bot, settings: Settings) -> None:
    if not is_public_https_url(settings.web_app_url):
        return
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text=MENU_BUTTON_TEXT,
            web_app=WebAppInfo(url=settings.web_app_url),
        )
    )


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Add it to .env")

    bot = Bot(settings.bot_token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(message: Message) -> None:
        await message.answer(
            build_start_text(),
            reply_markup=build_web_app_keyboard(settings),
        )

    @dp.message(Command("webapp"))
    async def webapp(message: Message) -> None:
        await message.answer(
            "Открой Telegram Web App кнопкой ниже:",
            reply_markup=build_web_app_keyboard(settings),
        )

    await configure_menu_button(bot, settings)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
