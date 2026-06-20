from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, Message, WebAppInfo

from app.config import Settings
from app.message_analysis import format_message_report

WEB_APP_BUTTON_TEXT = "Открыть анализатор"
MENU_BUTTON_TEXT = "Анализатор"
WEB_APP_COMMANDS = ("webapp", "pic")
BOT_COMMANDS = (
    BotCommand(command="start", description="Открыть описание и кнопку анализатора"),
    BotCommand(command="pic", description="Открыть мини-приложение анализатора"),
    BotCommand(command="webapp", description="Открыть Telegram Web App"),
)


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
        "Быстрый режим: просто пришли боту одно любое сообщение или фрагмент диалога в формате `Имя: текст` — "
        "он сразу вернёт мини-аналитику текста.\n\n"
        "Мини-приложение открывается кнопкой ниже. Там можно вставить переписку, а при необходимости загрузить result.json и получить разбор в более удобном интерфейсе.\n\n"
        "Важно: это эвристический скрининг по тексту, не психологический диагноз. Исходная переписка не публикуется."
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


async def configure_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(list(BOT_COMMANDS))


def build_dispatcher(settings: Settings) -> Dispatcher:
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(message: Message) -> None:
        await message.answer(
            build_start_text(),
            reply_markup=build_web_app_keyboard(settings),
        )

    @dp.message(Command(*WEB_APP_COMMANDS))
    async def webapp(message: Message) -> None:
        await message.answer(
            "Открой Telegram Web App кнопкой ниже:",
            reply_markup=build_web_app_keyboard(settings),
        )

    @dp.message()
    async def analyze_text_message(message: Message) -> None:
        if not message.text:
            await message.answer("Пришли текстовое сообщение — я сделаю быстрый мини-анализ.")
            return
        await message.answer(format_message_report(message.text), reply_markup=build_web_app_keyboard(settings))

    return dp
