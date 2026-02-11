"""Request service - business logic for money requests."""

from datetime import datetime, timedelta
from typing import NamedTuple
from zoneinfo import ZoneInfo

from sqlalchemy import and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from getmoney.config import settings
from getmoney.models import Request, RequestStatus


class MonthlyStats(NamedTuple):
    """Monthly statistics for requests."""

    requested: int  # Total requested amount
    approved: int  # Total approved (including sent, confirmed)
    confirmed: int  # Total confirmed received
    rejected: int  # Total rejected


class RequestService:
    """Service for managing money requests."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tz = ZoneInfo(settings.tz)

    async def create_request(
        self,
        user_id: int,
        amount: int,
        comment: str | None = None,
    ) -> Request:
        """Create a new money request."""
        request = Request(
            user_id=user_id,
            amount=amount,
            user_comment=comment,
            status=RequestStatus.PENDING,
        )
        self.session.add(request)
        await self.session.flush()
        await self.session.refresh(request)
        return request

    async def get_request(self, request_id: int) -> Request | None:
        """Get request by ID."""
        result = await self.session.execute(
            select(Request).where(Request.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_active_requests(self, user_id: int | None = None) -> list[Request]:
        """Get all active requests, optionally filtered by user."""
        query = select(Request).where(
            Request.status.in_([
                RequestStatus.PENDING,
                RequestStatus.APPROVED,
                RequestStatus.SENT,
                RequestStatus.DISPUTED,
            ])
        )
        if user_id:
            query = query.where(Request.user_id == user_id)
        query = query.order_by(Request.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_monthly_requests(
        self,
        user_id: int,
        year: int,
        month: int,
    ) -> list[Request]:
        """Get all requests for a specific month."""
        result = await self.session.execute(
            select(Request)
            .where(
                and_(
                    Request.user_id == user_id,
                    extract("year", Request.created_at) == year,
                    extract("month", Request.created_at) == month,
                )
            )
            .order_by(
                # Active first, then by date
                Request.status.in_([
                    RequestStatus.CONFIRMED,
                    RequestStatus.REJECTED,
                    RequestStatus.CANCELLED,
                ]),
                Request.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    async def get_monthly_stats(
        self,
        user_id: int,
        year: int,
        month: int,
    ) -> MonthlyStats:
        """Calculate monthly statistics."""
        requests = await self.get_monthly_requests(user_id, year, month)

        requested = sum(r.amount for r in requests)
        approved = sum(
            r.amount
            for r in requests
            if r.status_enum in (
                RequestStatus.APPROVED,
                RequestStatus.SENT,
                RequestStatus.CONFIRMED,
            )
        )
        confirmed = sum(
            r.amount for r in requests if r.status_enum == RequestStatus.CONFIRMED
        )
        rejected = sum(
            r.amount for r in requests if r.status_enum == RequestStatus.REJECTED
        )

        return MonthlyStats(
            requested=requested,
            approved=approved,
            confirmed=confirmed,
            rejected=rejected,
        )

    async def approve_request(
        self,
        request_id: int,
        eta: datetime,
        comment: str | None = None,
    ) -> Request | None:
        """Approve a request with ETA."""
        request = await self.get_request(request_id)
        if not request or request.status_enum != RequestStatus.PENDING:
            return None

        request.status = RequestStatus.APPROVED
        request.eta = eta
        if comment:
            request.admin_comment = comment

        await self.session.flush()
        return request

    async def reject_request(
        self,
        request_id: int,
        comment: str | None = None,
    ) -> Request | None:
        """Reject a request."""
        request = await self.get_request(request_id)
        if not request or request.status_enum not in (
            RequestStatus.PENDING,
            RequestStatus.APPROVED,
        ):
            return None

        request.status = RequestStatus.REJECTED
        if comment:
            request.admin_comment = comment

        await self.session.flush()
        return request

    async def mark_sent(self, request_id: int) -> Request | None:
        """Mark request as money sent."""
        request = await self.get_request(request_id)
        if not request or request.status_enum not in (
            RequestStatus.PENDING,
            RequestStatus.APPROVED,
            RequestStatus.DISPUTED,
        ):
            return None

        request.status = RequestStatus.SENT
        await self.session.flush()
        return request

    async def confirm_receipt(self, request_id: int) -> Request | None:
        """User confirms money receipt."""
        request = await self.get_request(request_id)
        if not request or request.status_enum != RequestStatus.SENT:
            return None

        request.status = RequestStatus.CONFIRMED
        await self.session.flush()
        return request

    async def dispute_receipt(self, request_id: int) -> Request | None:
        """User disputes money receipt (says not received)."""
        request = await self.get_request(request_id)
        if not request or request.status_enum != RequestStatus.SENT:
            return None

        request.status = RequestStatus.DISPUTED
        await self.session.flush()
        return request

    async def cancel_request(self, request_id: int) -> Request | None:
        """User cancels their request."""
        request = await self.get_request(request_id)
        if not request or not request.status_enum.can_cancel:
            return None

        request.status = RequestStatus.CANCELLED
        await self.session.flush()
        return request

    async def update_message_ids(
        self,
        request_id: int,
        user_message_id: int | None = None,
        admin_message_id: int | None = None,
    ) -> None:
        """Update stored message IDs for a request."""
        request = await self.get_request(request_id)
        if not request:
            return

        if user_message_id is not None:
            request.user_message_id = user_message_id
        if admin_message_id is not None:
            request.admin_message_id = admin_message_id

        await self.session.flush()

    def calculate_eta(self, option: str) -> datetime:
        """Calculate ETA datetime from option string."""
        now = datetime.now(self.tz)

        match option:
            case "1h":
                return now + timedelta(hours=1)
            case "today":
                # Today at 21:00
                return now.replace(hour=21, minute=0, second=0, microsecond=0)
            case "tomorrow":
                # Tomorrow at 12:00
                return (now + timedelta(days=1)).replace(
                    hour=12, minute=0, second=0, microsecond=0
                )
            case _:
                # Default: +24 hours
                return now + timedelta(hours=24)
