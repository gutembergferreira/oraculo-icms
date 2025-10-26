from __future__ import annotations
from functools import lru_cache
from typing import List, Optional
from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # evita "extra_forbidden"
    )

    # App/Base
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="Oraculo ICMS", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "oraculo-icms-api"

    # URLs gerais
    api_url: Optional[AnyHttpUrl] = Field(default=None, alias="API_URL")
    frontend_url: Optional[AnyHttpUrl] = Field(default=None, alias="FRONTEND_URL")

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    allowed_origins: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", "allowed_origins", mode="before")
    @classmethod
    def _parse_origins(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    # Banco / Redis
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    postgres_user: Optional[str] = Field(default=None, alias="POSTGRES_USER")
    postgres_password: Optional[str] = Field(default=None, alias="POSTGRES_PASSWORD")
    postgres_db: Optional[str] = Field(default=None, alias="POSTGRES_DB")
    postgres_host: Optional[str] = Field(default="db", alias="POSTGRES_HOST")
    postgres_port: Optional[int] = Field(default=5432, alias="POSTGRES_PORT")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    @field_validator("database_url", mode="after")
    def _ensure_database_url(cls, v, info):
        if v:
            return v
        d = info.data
        u, p, db = d.get("postgres_user"), d.get("postgres_password"), d.get("postgres_db")
        h = d.get("postgres_host") or "db"
        port = d.get("postgres_port") or 5432
        if u and p and db:
            return f"postgresql+psycopg://{u}:{p}@{h}:{port}/{db}"
        return v

    # JWT
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_access_expires: int = Field(default=900, alias="JWT_ACCESS_EXPIRES")
    jwt_refresh_expires: int = Field(default=604800, alias="JWT_REFRESH_EXPIRES")

    # Stripe
    stripe_public_key: Optional[str] = Field(default=None, alias="STRIPE_PUBLIC_KEY")
    stripe_secret_key: Optional[str] = Field(default=None, alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: Optional[str] = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")

    # Storage
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    local_storage_path: str = Field(default="/data/storage", alias="LOCAL_STORAGE_PATH")

    # Segurança / Observabilidade / Celery / Features
    fernet_key: Optional[str] = Field(default=None, alias="FERNET_KEY")
    rate_limit_per_minute: Optional[int] = Field(default=None, alias="RATE_LIMIT_PER_MINUTE")
    celery_broker_url: Optional[str] = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(default=None, alias="CELERY_RESULT_BACKEND")
    prometheus_multiproc_dir: Optional[str] = Field(default=None, alias="PROMETHEUS_MULTIPROC_DIR")
    feature_zfm_rules: Optional[bool] = Field(default=None, alias="FEATURE_ZFM_RULES")
    feature_webhook_outbound: Optional[bool] = Field(default=None, alias="FEATURE_WEBHOOK_OUTBOUND")

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
