"""SQLAlchemy async engine + sesión."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_engine_kwargs: dict = {}
if settings.database_url.startswith("postgresql"):
    _engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_async_engine(
    settings.database_url,
    echo=False,
    **_engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency para inyectar sesión async en los routers."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
