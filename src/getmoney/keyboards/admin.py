"""Admin keyboards."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from getmoney.models import Request, RequestStatus


class AdminKeyboards:
    """Keyboards for admin (husband)."""

    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Main menu keyboard for admin."""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Активные запросы")],
            ],
            resize_keyboard=True,
            is_persistent=True,
        )

    @staticmethod
    def new_request_actions(request_id: int) -> InlineKeyboardMarkup:
        """Actions for new incoming request."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Одобрить",
                        callback_data=f"admin:approve:{request_id}",
                    ),
                    InlineKeyboardButton(
                        text="💸 Отправлено",
                        callback_data=f"admin:sent:{request_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отклонить",
                        callback_data=f"admin:reject:{request_id}",
                    ),
                ],
            ]
        )

    @staticmethod
    def eta_selection(request_id: int) -> InlineKeyboardMarkup:
        """ETA selection keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⏱ Через 1 час",
                        callback_data=f"admin:eta:{request_id}:1h",
                    ),
                    InlineKeyboardButton(
                        text="🌙 Сегодня вечером",
                        callback_data=f"admin:eta:{request_id}:today",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="☀️ Завтра",
                        callback_data=f"admin:eta:{request_id}:tomorrow",
                    ),
                    InlineKeyboardButton(
                        text="✏️ Ввести вручную",
                        callback_data=f"admin:eta_manual:{request_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=f"admin:back:{request_id}",
                    ),
                ],
            ]
        )

    @staticmethod
    def approved_request_actions(request_id: int) -> InlineKeyboardMarkup:
        """Actions for approved request (waiting to send)."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💸 Отправлено",
                        callback_data=f"admin:sent:{request_id}",
                    ),
                ],
            ]
        )

    @staticmethod
    def disputed_request_actions(request_id: int) -> InlineKeyboardMarkup:
        """Actions for disputed request."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💸 Отправлено повторно",
                        callback_data=f"admin:sent:{request_id}",
                    ),
                ],
            ]
        )

    @staticmethod
    def request_actions(request: Request) -> InlineKeyboardMarkup | None:
        """Get appropriate keyboard for request status."""
        status = request.status_enum

        if status == RequestStatus.PENDING:
            return AdminKeyboards.new_request_actions(request.id)
        elif status == RequestStatus.APPROVED:
            return AdminKeyboards.approved_request_actions(request.id)
        elif status == RequestStatus.DISPUTED:
            return AdminKeyboards.disputed_request_actions(request.id)

        return None

    @staticmethod
    def reject_confirm(request_id: int) -> InlineKeyboardMarkup:
        """Confirm rejection keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Отклонить без комментария",
                        callback_data=f"admin:reject_confirm:{request_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="💬 Добавить причину",
                        callback_data=f"admin:reject_comment:{request_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=f"admin:back:{request_id}",
                    ),
                ],
            ]
        )
