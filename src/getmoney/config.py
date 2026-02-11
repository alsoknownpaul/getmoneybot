"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram Bot
    bot_token: str

    # User IDs
    admin_user_id: int
    user_user_id: int

    # Database
    database_url: str = "postgresql+asyncpg://getmoney:password@db:5432/getmoney"

    # Timezone
    tz: str = "Europe/Moscow"

    @property
    def allowed_user_ids(self) -> set[int]:
        """Get set of allowed user IDs."""
        return {self.admin_user_id, self.user_user_id}

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id == self.admin_user_id

    def is_user(self, user_id: int) -> bool:
        """Check if user is the regular user (wife)."""
        return user_id == self.user_user_id


settings = Settings()  # type: ignore[call-arg]
