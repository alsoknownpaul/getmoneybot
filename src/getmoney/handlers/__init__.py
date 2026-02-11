"""Telegram bot handlers."""

from aiogram import Router

from getmoney.handlers.user import router as user_router
from getmoney.handlers.admin import router as admin_router
from getmoney.handlers.common import router as common_router


def setup_routers() -> Router:
    """Setup and return main router with all handlers."""
    main_router = Router()

    # Include routers in order of priority
    main_router.include_router(common_router)
    main_router.include_router(admin_router)
    main_router.include_router(user_router)

    return main_router


__all__ = ["setup_routers"]
