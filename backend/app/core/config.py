from functools import lru_cache
from typing import Any

from pydantic import AnyHttpUrl, BaseSettings, Field


class Settings(BaseSettings):
    app_env: str = Field(default="development")
    app_name: str = Field(default="Oráculo ICMS")
    api_v1_prefix: str = Field(default="/api/v1")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_access_expires: int = Field(alias="JWT_ACCESS_EXPIRES", default=900)
    jwt_refresh_expires: int = Field(alias="JWT_REFRESH_EXPIRES", default=604800)

    stripe_public_key: str = Field(alias="STRIPE_PUBLIC_KEY")
    stripe_secret_key: str = Field(alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(alias="STRIPE_WEBHOOK_SECRET")

    storage_backend: str = Field(default="local")
    local_storage_path: str = Field(default="/data/storage")

    allowed_origins: list[AnyHttpUrl] = Field(
        default_factory=lambda: [AnyHttpUrl("http://localhost:3000")]
    )

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
