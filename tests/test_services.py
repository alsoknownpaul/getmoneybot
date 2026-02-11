"""Tests for services."""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import MagicMock, AsyncMock

from getmoney.services.request import RequestService


class TestRequestService:
    """Tests for RequestService."""

    def test_calculate_eta_1h(self) -> None:
        """Test ETA calculation for 1 hour."""
        session = MagicMock()
        service = RequestService(session)

        before = datetime.now(service.tz)
        eta = service.calculate_eta("1h")
        after = datetime.now(service.tz)

        # ETA should be approximately 1 hour from now
        assert eta >= before + timedelta(minutes=59)
        assert eta <= after + timedelta(hours=1, minutes=1)

    def test_calculate_eta_today(self) -> None:
        """Test ETA calculation for today."""
        session = MagicMock()
        service = RequestService(session)

        eta = service.calculate_eta("today")

        # Should be today at 21:00
        assert eta.hour == 21
        assert eta.minute == 0

    def test_calculate_eta_tomorrow(self) -> None:
        """Test ETA calculation for tomorrow."""
        session = MagicMock()
        service = RequestService(session)

        now = datetime.now(service.tz)
        eta = service.calculate_eta("tomorrow")

        # Should be tomorrow at 12:00
        assert eta.date() == (now + timedelta(days=1)).date()
        assert eta.hour == 12
        assert eta.minute == 0

    def test_calculate_eta_default(self) -> None:
        """Test ETA calculation for unknown option (default)."""
        session = MagicMock()
        service = RequestService(session)

        before = datetime.now(service.tz)
        eta = service.calculate_eta("unknown")

        # Default is +24 hours
        assert eta >= before + timedelta(hours=23, minutes=59)
