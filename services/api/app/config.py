from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_env: str = Field(default="dev", alias="APP_ENV")
    port: int = Field(default=8000, alias="PORT")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    esi_user_agent: str = Field(default="lostfits/0.1 (contact: you@example.com)", alias="ESI_USER_AGENT")
    esi_timeout_secs: int = Field(default=10, alias="ESI_TIMEOUT_SECS")
    esi_max_qps: int = Field(default=3, alias="ESI_MAX_QPS")

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()  # type: ignore
