from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from .models import Base
from contextlib import asynccontextmanager

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Auto-convert sync URL to async for app runtime (Alembic uses its own sync URL from alembic.ini)
def _to_async_url(url: str) -> str:
    if not url:
        return url
    # Common cases:
    # postgresql+psycopg2:// -> postgresql+asyncpg://
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + url.split("postgresql+psycopg2://", 1)[1]
    # plain postgresql:// -> postgresql+asyncpg://
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.split("postgresql://", 1)[1]
    return url

ASYNC_DATABASE_URL = _to_async_url(DATABASE_URL)
print(f"Using database connection (async): {ASYNC_DATABASE_URL}")

engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, 
)

@asynccontextmanager
async def get_session() -> AsyncSession:
    session = SessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        print(" ROLLBACK REASON:", repr(e))
        await session.rollback()
        raise e
    finally:
        await session.close()
