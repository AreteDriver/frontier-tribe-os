import sys

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = ""
    redis_url: str = "redis://localhost:6379"
    secret_key: str = ""
    environment: str = "development"

    # EVE Frontier SSO
    eve_frontier_client_id: str = ""
    eve_frontier_client_secret: str = ""
    eve_frontier_callback_url: str = "http://localhost:5173/auth/callback"

    # Sui
    sui_rpc_url: str = "https://fullnode.mainnet.sui.io:443"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # Discord
    discord_webhook_url: str = ""

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def validate_required_secrets(self) -> "Settings":
        """Fail fast if required secrets are missing in non-test environments."""
        if "pytest" in sys.modules:
            if not self.database_url:
                self.database_url = "sqlite+aiosqlite://"
            if not self.secret_key:
                self.secret_key = "test-secret-not-for-production"
            return self
        missing = []
        if not self.database_url:
            missing.append("DATABASE_URL")
        if (
            not self.secret_key
            or self.secret_key == "change-me-to-a-random-32-char-string-minimum"
        ):
            missing.append("SECRET_KEY")
        if self.environment != "development":
            if not self.eve_frontier_client_id:
                missing.append("EVE_FRONTIER_CLIENT_ID")
            if not self.eve_frontier_client_secret:
                missing.append("EVE_FRONTIER_CLIENT_SECRET")
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Copy .env.example to .env and fill in values."
            )
        return self


settings = Settings()
