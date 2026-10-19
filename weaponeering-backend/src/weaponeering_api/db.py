from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from weaponeering_api.config import get_settings


class Base(DeclarativeBase):
    """Base model สำหรับตารางของ web API (แยกจาก desktop maap_app)"""


settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def check_database() -> dict[str, str]:
    """ใช้ใน /health เพื่อตรวจว่าต่อ pgpool ได้"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "host": settings.db_host, "database": settings.db_name}
    except Exception as exc:  # noqa: BLE001 — surface connection errors in health
        return {
            "status": "error",
            "host": settings.db_host,
            "database": settings.db_name,
            "detail": str(exc),
        }
