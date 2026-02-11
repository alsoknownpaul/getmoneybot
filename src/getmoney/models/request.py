"""Money request model."""

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from getmoney.models.base import Base, TimestampMixin


class RequestStatus(str, Enum):
    """Request status enumeration."""

    PENDING = "pending"  # Waiting for admin action
    APPROVED = "approved"  # Approved with ETA
    SENT = "sent"  # Money sent, waiting for confirmation
    CONFIRMED = "confirmed"  # User confirmed receipt (final)
    REJECTED = "rejected"  # Admin rejected (final)
    CANCELLED = "cancelled"  # User cancelled (final)
    DISPUTED = "disputed"  # User says money not received

    @property
    def is_final(self) -> bool:
        """Check if status is final (no more actions possible)."""
        return self in (
            RequestStatus.CONFIRMED,
            RequestStatus.REJECTED,
            RequestStatus.CANCELLED,
        )

    @property
    def is_active(self) -> bool:
        """Check if request is active (requires attention)."""
        return not self.is_final

    @property
    def display_name(self) -> str:
        """Human-readable status name in Russian."""
        names = {
            RequestStatus.PENDING: "⏳ Ожидает",
            RequestStatus.APPROVED: "✅ Одобрено",
            RequestStatus.SENT: "💸 Отправлено",
            RequestStatus.CONFIRMED: "✔️ Получено",
            RequestStatus.REJECTED: "❌ Отклонено",
            RequestStatus.CANCELLED: "🚫 Отменено",
            RequestStatus.DISPUTED: "⚠️ Спорный",
        }
        return names.get(self, self.value)

    @property
    def can_cancel(self) -> bool:
        """Check if user can cancel this request."""
        return self in (RequestStatus.PENDING, RequestStatus.APPROVED)

    @property
    def can_remind(self) -> bool:
        """Check if user can send reminder for this request."""
        return self in (
            RequestStatus.PENDING,
            RequestStatus.APPROVED,
            RequestStatus.DISPUTED,
        )

    @property
    def can_confirm_receipt(self) -> bool:
        """Check if user can confirm receipt."""
        return self == RequestStatus.SENT

    @property
    def can_dispute(self) -> bool:
        """Check if user can dispute (say money not received)."""
        return self == RequestStatus.SENT


class Request(Base, TimestampMixin):
    """Money request model."""

    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RequestStatus] = mapped_column(
        String(20),
        default=RequestStatus.PENDING,
        nullable=False,
        index=True,
    )
    user_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Message IDs for updating inline keyboards
    user_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    admin_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<Request(id={self.id}, amount={self.amount}, status={self.status.value})>"

    @property
    def status_enum(self) -> RequestStatus:
        """Get status as enum (handles string from DB)."""
        if isinstance(self.status, RequestStatus):
            return self.status
        return RequestStatus(self.status)

    def format_amount(self) -> str:
        """Format amount with thousands separator."""
        return f"{self.amount:,}".replace(",", " ")

    def format_short(self) -> str:
        """Short format for lists."""
        return f"{self.format_amount()} ₽ — {self.status_enum.display_name}"

    def format_full(self, include_eta: bool = True) -> str:
        """Full format with all details."""
        lines = [
            f"💰 Сумма: {self.format_amount()} ₽",
            f"📊 Статус: {self.status_enum.display_name}",
        ]

        if include_eta and self.eta and self.status_enum == RequestStatus.APPROVED:
            lines.append(f"⏰ ETA: {self.eta.strftime('%d.%m.%Y %H:%M')}")

        if self.user_comment:
            lines.append(f"💬 Комментарий: {self.user_comment}")

        if self.admin_comment:
            lines.append(f"📝 От админа: {self.admin_comment}")

        lines.append(f"📅 Создан: {self.created_at.strftime('%d.%m.%Y %H:%M')}")

        return "\n".join(lines)
