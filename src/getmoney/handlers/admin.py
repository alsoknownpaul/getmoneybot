"""Admin (husband) handlers."""

from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from getmoney.config import settings
from getmoney.db import get_session
from getmoney.keyboards import AdminKeyboards
from getmoney.services import RequestService

router = Router()


class AdminStates(StatesGroup):
    """FSM states for admin actions."""

    waiting_for_eta = State()
    waiting_for_reject_comment = State()


# === Main Menu ===


@router.message(
    F.text == "📋 Активные запросы",
    F.from_user.id == settings.admin_user_id,
)
async def show_active_requests(message: Message) -> None:
    """Show all active requests."""
    async with get_session() as session:
        service = RequestService(session)
        requests = await service.get_active_requests()

    if not requests:
        await message.answer("✅ Нет активных запросов.")
        return

    text = "📋 Активные запросы:\n\n"
    for r in requests:
        text += f"#{r.id} — {r.format_amount()} ₽ — {r.status_enum.display_name}\n"

    await message.answer(text)

    # Send each request with action buttons
    for r in requests:
        keyboard = AdminKeyboards.request_actions(r)
        if keyboard:
            await message.answer(
                f"📝 Запрос #{r.id}\n\n{r.format_full()}",
                reply_markup=keyboard,
            )


@router.message(
    Command("active"),
    F.from_user.id == settings.admin_user_id,
)
async def cmd_active(message: Message) -> None:
    """Command to show active requests."""
    await show_active_requests(message)


# === Approve Flow ===


@router.callback_query(
    F.data.startswith("admin:approve:"),
    F.from_user.id == settings.admin_user_id,
)
async def start_approve(callback: CallbackQuery) -> None:
    """Start approval - show ETA options."""
    request_id = int(callback.data.split(":")[2])

    await callback.message.edit_reply_markup(
        reply_markup=AdminKeyboards.eta_selection(request_id)
    )
    await callback.answer()


@router.callback_query(
    F.data.startswith("admin:eta:"),
    F.from_user.id == settings.admin_user_id,
)
async def select_eta(callback: CallbackQuery, bot: Bot) -> None:
    """Handle ETA selection."""
    parts = callback.data.split(":")
    request_id = int(parts[2])
    eta_option = parts[3]

    async with get_session() as session:
        service = RequestService(session)
        eta = service.calculate_eta(eta_option)
        request = await service.approve_request(request_id, eta)

        if not request:
            await callback.answer("❌ Ошибка при одобрении", show_alert=True)
            return

        # Notify user
        await bot.send_message(
            chat_id=settings.user_user_id,
            text=(
                f"✅ Запрос #{request.id} одобрен!\n\n"
                f"💰 Сумма: {request.format_amount()} ₽\n"
                f"⏰ ETA: {eta.strftime('%d.%m.%Y %H:%M')}"
            ),
        )

    # Update admin message
    await callback.message.edit_text(
        f"✅ Запрос #{request_id} одобрен!\n"
        f"⏰ ETA: {eta.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Когда отправишь — нажми кнопку ниже.",
        reply_markup=AdminKeyboards.approved_request_actions(request_id),
    )
    await callback.answer("Одобрено!")


@router.callback_query(
    F.data.startswith("admin:eta_manual:"),
    F.from_user.id == settings.admin_user_id,
)
async def ask_manual_eta(callback: CallbackQuery, state: FSMContext) -> None:
    """Ask for manual ETA input."""
    request_id = int(callback.data.split(":")[2])
    await state.update_data(request_id=request_id)
    await state.set_state(AdminStates.waiting_for_eta)

    await callback.message.edit_text(
        f"📝 Запрос #{request_id}\n\n"
        "Введи дату и время (формат: ДД.ММ.ГГГГ ЧЧ:ММ или ДД.ММ ЧЧ:ММ):"
    )
    await callback.answer()


@router.message(
    AdminStates.waiting_for_eta,
    F.from_user.id == settings.admin_user_id,
)
async def receive_manual_eta(message: Message, state: FSMContext, bot: Bot) -> None:
    """Receive manual ETA input."""
    data = await state.get_data()
    request_id = data.get("request_id")

    tz = ZoneInfo(settings.tz)
    now = datetime.now(tz)

    # Try to parse datetime
    text = message.text.strip()
    eta = None

    formats = [
        "%d.%m.%Y %H:%M",
        "%d.%m %H:%M",
        "%d.%m.%Y",
        "%d.%m",
    ]

    for fmt in formats:
        try:
            eta = datetime.strptime(text, fmt)
            # Add year if not specified
            if eta.year == 1900:
                eta = eta.replace(year=now.year)
            # Add timezone
            eta = eta.replace(tzinfo=tz)
            break
        except ValueError:
            continue

    if not eta:
        await message.answer(
            "❌ Неверный формат. Используй: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Например: 25.12.2024 18:00"
        )
        return

    async with get_session() as session:
        service = RequestService(session)
        request = await service.approve_request(request_id, eta)

        if not request:
            await message.answer("❌ Ошибка при одобрении")
            await state.clear()
            return

        # Notify user
        await bot.send_message(
            chat_id=settings.user_user_id,
            text=(
                f"✅ Запрос #{request.id} одобрен!\n\n"
                f"💰 Сумма: {request.format_amount()} ₽\n"
                f"⏰ ETA: {eta.strftime('%d.%m.%Y %H:%M')}"
            ),
        )

    await state.clear()
    await message.answer(
        f"✅ Запрос #{request_id} одобрен!\n"
        f"⏰ ETA: {eta.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Когда отправишь — нажми кнопку ниже.",
        reply_markup=AdminKeyboards.approved_request_actions(request_id),
    )


# === Sent ===


@router.callback_query(
    F.data.startswith("admin:sent:"),
    F.from_user.id == settings.admin_user_id,
)
async def mark_sent(callback: CallbackQuery, bot: Bot) -> None:
    """Mark request as money sent."""
    request_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        service = RequestService(session)
        request = await service.mark_sent(request_id)

        if not request:
            await callback.answer("❌ Ошибка", show_alert=True)
            return

        # Notify user with confirmation buttons
        from getmoney.keyboards import UserKeyboards

        await bot.send_message(
            chat_id=settings.user_user_id,
            text=(
                f"💸 Средства отправлены!\n\n"
                f"Запрос #{request.id}: {request.format_amount()} ₽\n\n"
                f"Пожалуйста, подтверди получение."
            ),
            reply_markup=UserKeyboards.request_actions(request),
        )

    await callback.message.edit_text(
        f"💸 Запрос #{request_id} — средства отправлены.\n\n"
        f"Ожидаем подтверждение получения."
    )
    await callback.answer("Отмечено как отправленное!")


# === Reject Flow ===


@router.callback_query(
    F.data.startswith("admin:reject:"),
    F.from_user.id == settings.admin_user_id,
)
async def start_reject(callback: CallbackQuery) -> None:
    """Start rejection flow."""
    request_id = int(callback.data.split(":")[2])

    await callback.message.edit_reply_markup(
        reply_markup=AdminKeyboards.reject_confirm(request_id)
    )
    await callback.answer()


@router.callback_query(
    F.data.startswith("admin:reject_confirm:"),
    F.from_user.id == settings.admin_user_id,
)
async def confirm_reject(callback: CallbackQuery, bot: Bot) -> None:
    """Reject without comment."""
    request_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        service = RequestService(session)
        request = await service.reject_request(request_id)

        if not request:
            await callback.answer("❌ Ошибка", show_alert=True)
            return

        # Notify user
        await bot.send_message(
            chat_id=settings.user_user_id,
            text=f"❌ Запрос #{request.id} на {request.format_amount()} ₽ отклонён.",
        )

    await callback.message.edit_text(f"❌ Запрос #{request_id} отклонён.")
    await callback.answer()


@router.callback_query(
    F.data.startswith("admin:reject_comment:"),
    F.from_user.id == settings.admin_user_id,
)
async def ask_reject_comment(callback: CallbackQuery, state: FSMContext) -> None:
    """Ask for rejection reason."""
    request_id = int(callback.data.split(":")[2])
    await state.update_data(request_id=request_id)
    await state.set_state(AdminStates.waiting_for_reject_comment)

    await callback.message.edit_text(
        f"📝 Запрос #{request_id}\n\nВведи причину отклонения:"
    )
    await callback.answer()


@router.message(
    AdminStates.waiting_for_reject_comment,
    F.from_user.id == settings.admin_user_id,
)
async def receive_reject_comment(message: Message, state: FSMContext, bot: Bot) -> None:
    """Receive rejection comment and reject."""
    data = await state.get_data()
    request_id = data.get("request_id")
    comment = message.text[:500] if message.text else None

    async with get_session() as session:
        service = RequestService(session)
        request = await service.reject_request(request_id, comment)

        if not request:
            await message.answer("❌ Ошибка при отклонении")
            await state.clear()
            return

        # Notify user
        text = f"❌ Запрос #{request.id} на {request.format_amount()} ₽ отклонён."
        if comment:
            text += f"\n\n💬 Причина: {comment}"

        await bot.send_message(chat_id=settings.user_user_id, text=text)

    await state.clear()
    await message.answer(f"❌ Запрос #{request_id} отклонён с комментарием.")


# === Back Navigation ===


@router.callback_query(
    F.data.startswith("admin:back:"),
    F.from_user.id == settings.admin_user_id,
)
async def go_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Go back to original request actions."""
    await state.clear()
    request_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        service = RequestService(session)
        request = await service.get_request(request_id)

        if not request:
            await callback.answer("❌ Запрос не найден", show_alert=True)
            return

        await callback.message.edit_text(
            f"📝 Запрос #{request.id}\n\n{request.format_full()}",
            reply_markup=AdminKeyboards.request_actions(request),
        )
    await callback.answer()
