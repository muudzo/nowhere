from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# Engine
# We use echo=False to reduce noise, can be True for debugging
engine = create_async_engine(settings.postgres_url, echo=False)

# Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    expire_on_commit=False,
    class_=AsyncSession
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    # For MVP, we can use create_all. For prod, use Alembic.
    # We will try to create tables if we can connect.
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized (if connection successful).")
    except Exception as e:
        logger.warning(f"Failed to initialize DB (Postgres might be down): {e}")
