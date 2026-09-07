from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import settings

async_engine = create_async_engine(settings.DATABASE_URL_ASYNC, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

sync_engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)