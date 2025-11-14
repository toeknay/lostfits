from functools import lru_cache
from typing import cast

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ESI_DEFAULT = cast(AnyHttpUrl, "https://esi.evetech.net/latest")


class Settings(BaseSettings):
    app_env: str = Field(default="dev", alias="APP_ENV")
    port: int = Field(default=8000, alias="PORT")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        alias="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins",
    )

    # Admin API key for protecting admin endpoints
    admin_api_key: str | None = Field(
        default=None, alias="ADMIN_API_KEY", description="API key for admin endpoints"
    )

    # ESI-related
    esi_user_agent: str = Field(
        default="lostfits/0.1 (contact: you@example.com)", alias="ESI_USER_AGENT"
    )
    esi_timeout_secs: int = Field(default=10, alias="ESI_TIMEOUT_SECS")
    esi_max_qps: int = Field(default=3, alias="ESI_MAX_QPS")
    esi_base: AnyHttpUrl = Field(default=ESI_DEFAULT, alias="ESI_BASE")

    # zKill (optional)
    zkill_stream_url: AnyHttpUrl | None = Field(default=None, alias="ZKILL_STREAM_URL")

    # pydantic v2 style config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
