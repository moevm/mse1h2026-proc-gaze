from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from src.util.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=True,
    pool_size=10,
    max_overflow=10,
)

SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
