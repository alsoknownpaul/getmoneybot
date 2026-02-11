"""User keyboards."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from getmoney.models import Request, RequestStatus


class UserKeyboards:
    """Keyboards for regular user (wife)."""

    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Main menu keyboard."""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💰 Запросить средства")],
                [
                    KeyboardButton(text="📋 Мои запросы (этот месяц)"),
                    KeyboardButton(text="📋 Прошлый месяц"),
                ],
            ],
            resize_keyboard=True,
            is_persistent=True,
        )

    @staticmethod
    def amount_selection() -> InlineKeyboardMarkup:
        """Amount selection keyboard."""
        amounts = [5000, 10000, 15000, 20000, 30000, 50000]
        buttons = []

        # Two buttons per row
        for i in range(0, len(amounts), 2):
            row = []
            for amount in amounts[i : i + 2]:
                row.append(
                    InlineKeyboardButton(
                        text=f"{amount:,}₽".replace(",", " "),
                        callback_data=f"amount:{amount}",
                    )
                )
            buttons.append(row)

        # Cancel button
        buttons.append([
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_request_flow")
        ])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def confirm_request(amount: int) -> InlineKeyboardMarkup:
        """Confirm request keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Да, запросить",
                        callback_data=f"confirm_request:{amount}",
                    ),
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data="cancel_request_flow",
                    ),
                ],
            ]
        )

    @staticmethod
    def add_comment(amount: int) -> InlineKeyboardMarkup:
        """Ask if user wants to add comment."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 Добавить комментарий",
                        callback_data=f"add_comment:{amount}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Отправить без комментария",
                        callback_data=f"confirm_request:{amount}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data="cancel_request_flow",
                    ),
                ],
            ]
        )

    @staticmethod
    def request_actions(request: Request) -> InlineKeyboardMarkup | None:
        """Actions keyboard for a request based on its status."""
        status = request.status_enum
        buttons = []

        if status.can_remind:
            buttons.append([
                InlineKeyboardButton(
                    text="🔔 Напомнить",
                    callback_data=f"remind:{request.id}",
                )
            ])

        if status.can_cancel:
            buttons.append([
                InlineKeyboardButton(
                    text="🚫 Отменить запрос",
                    callback_data=f"cancel:{request.id}",
                )
            ])

        if status.can_confirm_receipt:
            buttons.append([
                InlineKeyboardButton(
                    text="✅ Подтвердить получение",
                    callback_data=f"confirm_receipt:{request.id}",
                ),
            ])
            buttons.append([
                InlineKeyboardButton(
                    text="❌ Деньги не пришли",
                    callback_data=f"dispute:{request.id}",
                ),
            ])

        if not buttons:
            return None

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def back_to_list() -> InlineKeyboardMarkup:
        """Back to requests list."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ К списку запросов",
                        callback_data="back_to_list",
                    )
                ]
            ]
        )
