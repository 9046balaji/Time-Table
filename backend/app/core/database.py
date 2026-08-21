from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def ensure_database() -> None:
    """Create all table definitions registered in the app metadata.

    This guard prevents requests from failing when the app is being exercised via
    ASGITransport or any startup path that does not trigger the FastAPI lifespan
    hook.
    """
    import app.models  # noqa: F401  # ensure all metadata is imported before create_all

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS iteration INTEGER DEFAULT 1 NOT NULL;"))
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS total_iterations INTEGER DEFAULT 1 NOT NULL;"))
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS approval_required BOOLEAN DEFAULT FALSE NOT NULL;"))
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS approval_status VARCHAR(30) DEFAULT 'none' NOT NULL;"))
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS completed_actions JSON DEFAULT '[]'::json NOT NULL;"))
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS failed_actions JSON DEFAULT '[]'::json NOT NULL;"))
    except (RuntimeError, Exception):
        await engine.dispose()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS iteration INTEGER DEFAULT 1 NOT NULL;"))
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS total_iterations INTEGER DEFAULT 1 NOT NULL;"))
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS approval_required BOOLEAN DEFAULT FALSE NOT NULL;"))
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS approval_status VARCHAR(30) DEFAULT 'none' NOT NULL;"))
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS completed_actions JSON DEFAULT '[]'::json NOT NULL;"))
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS failed_actions JSON DEFAULT '[]'::json NOT NULL;"))


async def get_db():
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    except (RuntimeError, Exception):
        await engine.dispose()
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
