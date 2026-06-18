import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from app.config import get_settings


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Add it to .env")

    bot = Bot(settings.bot_token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(message: Message) -> None:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Открыть анализатор",
                        web_app=WebAppInfo(url=settings.web_app_url),
                    )
                ]
            ]
        )
        await message.answer(
            "Загрузи Telegram result.json и получи аналитику переписки.",
            reply_markup=keyboard,
        )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
