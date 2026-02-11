"""Common handlers (start, help, access control)."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from getmoney.config import settings
from getmoney.keyboards import UserKeyboards, AdminKeyboards

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    user_id = message.from_user.id if message.from_user else 0

    if user_id not in settings.allowed_user_ids:
        await message.answer(
            "⛔ Доступ запрещён.\n"
            "Этот бот работает только для авторизованных пользователей."
        )
        return

    if settings.is_admin(user_id):
        await message.answer(
            "👋 Привет, админ!\n\n"
            "Здесь ты будешь получать запросы на средства.\n"
            "Используй кнопку ниже для просмотра активных запросов.",
            reply_markup=AdminKeyboards.main_menu(),
        )
    else:
        await message.answer(
            "👋 Привет!\n\n"
            "Этот бот поможет тебе запрашивать средства.\n"
            "Используй кнопки ниже:",
            reply_markup=UserKeyboards.main_menu(),
        )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    user_id = message.from_user.id if message.from_user else 0

    if settings.is_admin(user_id):
        text = (
            "📖 Справка (Админ)\n\n"
            "• Ты получаешь уведомления о новых запросах\n"
            "• Можешь одобрить, отклонить или сразу отметить как отправленное\n"
            "• При одобрении укажи ETA - когда средства будут отправлены\n"
            "• Используй /active для просмотра всех активных запросов"
        )
    else:
        text = (
            "📖 Справка\n\n"
            "• 💰 Запросить средства - создать новый запрос\n"
            "• 📋 Мои запросы - посмотреть историю\n\n"
            "После отправки запроса ты получишь уведомление о решении."
        )

    await message.answer(text)


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    """Show user's Telegram ID (useful for setup)."""
    user_id = message.from_user.id if message.from_user else 0
    await message.answer(f"🆔 Твой Telegram ID: `{user_id}`", parse_mode="Markdown")
