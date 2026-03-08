from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://tribeuser:tribepass@localhost:5432/tribedb"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "change-me-to-a-random-32-char-string-minimum"
    environment: str = "development"

    # EVE Frontier SSO
    eve_frontier_client_id: str = ""
    eve_frontier_client_secret: str = ""
    eve_frontier_callback_url: str = "http://localhost:8000/auth/callback"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
