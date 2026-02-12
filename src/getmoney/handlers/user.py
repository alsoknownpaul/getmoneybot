"""User (wife) handlers."""

from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from getmoney.config import settings
from getmoney.db import get_session
from getmoney.keyboards import UserKeyboards
from getmoney.keyboards.admin import AdminKeyboards
from getmoney.services import RequestService

router = Router()

# Filter: only allow the regular user (wife)
router.message.filter(F.from_user.id == settings.user_user_id)
router.callback_query.filter(F.from_user.id == settings.user_user_id)


class RequestStates(StatesGroup):
    """FSM states for request creation."""

    waiting_for_amount = State()
    waiting_for_comment = State()
    confirming = State()


# === Request Creation Flow ===


@router.message(F.text == "💰 Запросить средства")
async def start_request(message: Message, state: FSMContext) -> None:
    """Start money request flow."""
    await state.set_state(RequestStates.waiting_for_amount)
    await message.answer(
        "💰 Выбери сумму или введи свою:",
        reply_markup=UserKeyboards.amount_selection(),
    )


@router.callback_query(F.data.startswith("amount:"))
async def select_amount(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle amount button selection."""
    amount = int(callback.data.split(":")[1])
    await state.update_data(amount=amount)
    await state.set_state(RequestStates.confirming)

    await callback.message.edit_text(
        f"💰 Сумма: {amount:,} ₽\n\nДобавить комментарий?".replace(",", " "),
        reply_markup=UserKeyboards.add_comment(amount),
    )
    await callback.answer()


@router.message(RequestStates.waiting_for_amount, F.text.regexp(r"^\d+$"))
async def enter_custom_amount(message: Message, state: FSMContext) -> None:
    """Handle custom amount text input."""
    amount = int(message.text)

    if amount < 100:
        await message.answer("❌ Минимальная сумма: 100 ₽")
        return

    if amount > 10_000_000:
        await message.answer("❌ Максимальная сумма: 10 000 000 ₽")
        return

    await state.update_data(amount=amount)
    await state.set_state(RequestStates.confirming)

    await message.answer(
        f"💰 Сумма: {amount:,} ₽\n\nДобавить комментарий?".replace(",", " "),
        reply_markup=UserKeyboards.add_comment(amount),
    )


@router.callback_query(F.data.startswith("add_comment:"))
async def ask_for_comment(callback: CallbackQuery, state: FSMContext) -> None:
    """Ask user to enter comment."""
    await state.set_state(RequestStates.waiting_for_comment)
    await callback.message.edit_text(
        "💬 Введи комментарий к запросу:"
    )
    await callback.answer()


@router.message(RequestStates.waiting_for_comment)
async def receive_comment(message: Message, state: FSMContext) -> None:
    """Receive comment and confirm."""
    comment = message.text[:500] if message.text else None
    data = await state.get_data()
    amount = data.get("amount", 0)

    await state.update_data(comment=comment)

    await message.answer(
        f"💰 Сумма: {amount:,} ₽\n💬 Комментарий: {comment}\n\nОтправить запрос?".replace(
            ",", " "
        ),
        reply_markup=UserKeyboards.confirm_request(amount),
    )


@router.callback_query(F.data.startswith("confirm_request:"))
async def confirm_request(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Confirm and create request."""
    data = await state.get_data()
    amount = data.get("amount") or int(callback.data.split(":")[1])
    comment = data.get("comment")

    user_id = callback.from_user.id

    async with get_session() as session:
        service = RequestService(session)
        request = await service.create_request(
            user_id=user_id,
            amount=amount,
            comment=comment,
        )

        # Notify admin
        admin_text = (
            f"🆕 Новый запрос #{request.id}\n\n"
            f"💰 Сумма: {request.format_amount()} ₽\n"
        )
        if comment:
            admin_text += f"💬 Комментарий: {comment}\n"
        admin_text += f"📅 {request.created_at.strftime('%d.%m.%Y %H:%M')}"

        admin_msg = await bot.send_message(
            chat_id=settings.admin_user_id,
            text=admin_text,
            reply_markup=AdminKeyboards.new_request_actions(request.id),
        )

        # Save message IDs
        await service.update_message_ids(
            request.id,
            admin_message_id=admin_msg.message_id,
        )

    await state.clear()
    await callback.message.edit_text(
        f"✅ Запрос на {amount:,} ₽ отправлен!\n\n"
        "Ты получишь уведомление, когда запрос будет обработан.".replace(",", " ")
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_request_flow")
async def cancel_request_flow(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancel request creation."""
    await state.clear()
    await callback.message.edit_text("❌ Запрос отменён.")
    await callback.answer()


# === View Requests ===


@router.message(F.text.in_(["📋 Мои запросы (этот месяц)", "📋 Прошлый месяц"]))
async def show_requests(message: Message) -> None:
    """Show user's requests for month."""
    user_id = message.from_user.id if message.from_user else 0
    tz = ZoneInfo(settings.tz)
    now = datetime.now(tz)

    if "Прошлый" in message.text:
        # Previous month
        if now.month == 1:
            year, month = now.year - 1, 12
        else:
            year, month = now.year, now.month - 1
        month_name = "прошлый месяц"
    else:
        year, month = now.year, now.month
        month_name = "этот месяц"

    async with get_session() as session:
        service = RequestService(session)
        requests = await service.get_monthly_requests(user_id, year, month)
        stats = await service.get_monthly_stats(user_id, year, month)

    if not requests:
        await message.answer(f"📋 Нет запросов за {month_name}.")
        return

    # Format requests list
    lines = [f"📋 Запросы за {month_name}:\n"]

    # Active requests first
    active = [r for r in requests if r.status_enum.is_active]
    completed = [r for r in requests if not r.status_enum.is_active]

    if active:
        lines.append("🔔 Активные:")
        for r in active:
            day_name = r.created_at.strftime("%a")
            lines.append(
                f"  • {r.created_at.strftime('%d.%m')} ({day_name}) — "
                f"{r.format_amount()} ₽ — {r.status_enum.display_name}"
            )
            if r.status_enum.can_confirm_receipt:
                lines.append("    ⬆️ Нажми для подтверждения получения")
        lines.append("")

    if completed:
        lines.append("📜 Завершённые:")
        for r in completed[:10]:  # Last 10
            day_name = r.created_at.strftime("%a")
            lines.append(
                f"  • {r.created_at.strftime('%d.%m')} ({day_name}) — "
                f"{r.format_amount()} ₽ — {r.status_enum.display_name}"
            )
        if len(completed) > 10:
            lines.append(f"  ... и ещё {len(completed) - 10}")
        lines.append("")

    # Statistics
    lines.append("📊 Итого:")
    lines.append(f"  💰 Запрошено: {stats.requested:,} ₽".replace(",", " "))
    lines.append(f"  ✅ Одобрено: {stats.approved:,} ₽".replace(",", " "))
    lines.append(f"  ✔️ Получено: {stats.confirmed:,} ₽".replace(",", " "))
    if stats.rejected:
        lines.append(f"  ❌ Отклонено: {stats.rejected:,} ₽".replace(",", " "))

    text = "\n".join(lines)

    # Send summary message
    await message.answer(text)

    # Send each active request with action buttons (like admin view)
    actionable = [r for r in active if r.status_enum.can_cancel or r.status_enum.can_confirm_receipt or r.status_enum.can_remind]
    for r in actionable:
        keyboard = UserKeyboards.request_actions(r)
        if keyboard:
            await message.answer(
                f"📝 Запрос #{r.id}:\n{r.format_full()}",
                reply_markup=keyboard,
            )


# === Request Actions ===


@router.callback_query(F.data.startswith("remind:"))
async def remind_admin(callback: CallbackQuery, bot: Bot) -> None:
    """Send reminder to admin."""
    request_id = int(callback.data.split(":")[1])

    async with get_session() as session:
        service = RequestService(session)
        request = await service.get_request(request_id)

        if not request or not request.status_enum.can_remind:
            await callback.answer("❌ Нельзя отправить напоминание", show_alert=True)
            return

        # Send reminder to admin
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text=(
                f"🔔 Напоминание о запросе #{request.id}\n\n"
                f"{request.format_full()}"
            ),
            reply_markup=AdminKeyboards.request_actions(request),
        )

    await callback.answer("✅ Напоминание отправлено!")


@router.callback_query(F.data.startswith("cancel:"))
async def cancel_request(callback: CallbackQuery, bot: Bot) -> None:
    """Cancel a request."""
    request_id = int(callback.data.split(":")[1])

    async with get_session() as session:
        service = RequestService(session)
        request = await service.cancel_request(request_id)

        if not request:
            await callback.answer("❌ Нельзя отменить этот запрос", show_alert=True)
            return

        # Notify admin
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text=f"🚫 Запрос #{request.id} отменён пользователем.\n\n{request.format_full()}",
        )

    await callback.message.edit_text(
        f"🚫 Запрос #{request_id} отменён."
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_receipt:"))
async def confirm_receipt(callback: CallbackQuery, bot: Bot) -> None:
    """Confirm money receipt."""
    request_id = int(callback.data.split(":")[1])

    async with get_session() as session:
        service = RequestService(session)
        request = await service.confirm_receipt(request_id)

        if not request:
            await callback.answer("❌ Нельзя подтвердить этот запрос", show_alert=True)
            return

        # Notify admin
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text=f"✅ Получение подтверждено!\n\nЗапрос #{request.id}: {request.format_amount()} ₽",
        )

    await callback.message.edit_text(
        f"✅ Получение {request.format_amount()} ₽ подтверждено!\n\nСпасибо! 💕"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dispute:"))
async def dispute_receipt(callback: CallbackQuery, bot: Bot) -> None:
    """Dispute money receipt (not received)."""
    request_id = int(callback.data.split(":")[1])

    async with get_session() as session:
        service = RequestService(session)
        request = await service.dispute_receipt(request_id)

        if not request:
            await callback.answer("❌ Ошибка", show_alert=True)
            return

        # Notify admin urgently
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text=(
                f"⚠️ ВНИМАНИЕ: Деньги не получены!\n\n"
                f"Запрос #{request.id}: {request.format_amount()} ₽\n\n"
                f"Пользователь сообщает, что средства не поступили."
            ),
            reply_markup=AdminKeyboards.disputed_request_actions(request.id),
        )

    await callback.message.edit_text(
        f"⚠️ Сообщение о том, что деньги не пришли, отправлено.\n\n"
        f"Запрос #{request_id} отмечен как спорный."
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: CallbackQuery) -> None:
    """Return to requests list."""
    await callback.message.delete()
    await callback.answer()
