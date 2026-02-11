"""Tests for models."""

import pytest
from getmoney.models import RequestStatus


class TestRequestStatus:
    """Tests for RequestStatus enum."""

    def test_is_final(self) -> None:
        """Test is_final property."""
        assert RequestStatus.CONFIRMED.is_final is True
        assert RequestStatus.REJECTED.is_final is True
        assert RequestStatus.CANCELLED.is_final is True
        assert RequestStatus.PENDING.is_final is False
        assert RequestStatus.APPROVED.is_final is False
        assert RequestStatus.SENT.is_final is False
        assert RequestStatus.DISPUTED.is_final is False

    def test_is_active(self) -> None:
        """Test is_active property."""
        assert RequestStatus.PENDING.is_active is True
        assert RequestStatus.APPROVED.is_active is True
        assert RequestStatus.SENT.is_active is True
        assert RequestStatus.DISPUTED.is_active is True
        assert RequestStatus.CONFIRMED.is_active is False
        assert RequestStatus.REJECTED.is_active is False
        assert RequestStatus.CANCELLED.is_active is False

    def test_can_cancel(self) -> None:
        """Test can_cancel property."""
        assert RequestStatus.PENDING.can_cancel is True
        assert RequestStatus.APPROVED.can_cancel is True
        assert RequestStatus.SENT.can_cancel is False
        assert RequestStatus.DISPUTED.can_cancel is False

    def test_can_confirm_receipt(self) -> None:
        """Test can_confirm_receipt property."""
        assert RequestStatus.SENT.can_confirm_receipt is True
        assert RequestStatus.PENDING.can_confirm_receipt is False
        assert RequestStatus.APPROVED.can_confirm_receipt is False

    def test_can_dispute(self) -> None:
        """Test can_dispute property."""
        assert RequestStatus.SENT.can_dispute is True
        assert RequestStatus.PENDING.can_dispute is False

    def test_display_name(self) -> None:
        """Test display_name property."""
        assert "Ожидает" in RequestStatus.PENDING.display_name
        assert "Одобрено" in RequestStatus.APPROVED.display_name
        assert "Отправлено" in RequestStatus.SENT.display_name
