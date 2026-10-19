from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Weaponeering API"
    api_prefix: str = "/api"
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    # PostgreSQL via pgpool (same pattern as service-complaint)
    db_host: str = "pgpool"
    db_port: int = 5432
    db_name: str = "weaponeering"
    db_user: str = ""
    db_password: str = ""

    rtaf_mfa_url: str = "https://apigw.rtaf.mi.th/login-rtaf-mfa/v2/mfa/login"
    rtaf_mfa_timeout_seconds: float = 15.0
    # apigw.rtaf.mi.th ใช้ cert ภายใน — ปิด verify ใน Docker/dev (เหมือน MINIO_CERT_CHECK=false)
    rtaf_mfa_verify_ssl: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def database_url(self) -> str:
        """Async SQLAlchemy URL through pgpool."""
        user = self.db_user or "postgres"
        password = self.db_password or ""
        auth = f"{user}:{password}@" if password else f"{user}@"
        return (
            f"postgresql+asyncpg://{auth}{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync URL (Alembic / utilities)."""
        user = self.db_user or "postgres"
        password = self.db_password or ""
        auth = f"{user}:{password}@" if password else f"{user}@"
        return f"postgresql+psycopg://{auth}{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
