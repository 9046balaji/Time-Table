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

_default_sessionmaker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
_CURRENT_SESSION_MAKER = _default_sessionmaker

class _SessionLocalProxy:
    def __call__(self, *args, **kwargs):
        return _CURRENT_SESSION_MAKER(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(_CURRENT_SESSION_MAKER, name)

AsyncSessionLocal = _SessionLocalProxy()
async_session_factory = _SessionLocalProxy()

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
            if conn.dialect.name == "postgresql":
                from sqlalchemy import text
                await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS iteration INTEGER DEFAULT 1 NOT NULL;"))
                await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS total_iterations INTEGER DEFAULT 1 NOT NULL;"))
                await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS approval_required BOOLEAN DEFAULT FALSE NOT NULL;"))
                await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS approval_status VARCHAR(30) DEFAULT 'none' NOT NULL;"))
                await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS completed_actions JSON DEFAULT '[]'::json NOT NULL;"))
                await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS failed_actions JSON DEFAULT '[]'::json NOT NULL;"))
                await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS session_timeout_at TIMESTAMP WITHOUT TIME ZONE;"))
                await conn.execute(text("ALTER TABLE agent_events ADD COLUMN IF NOT EXISTS sequence_number INTEGER DEFAULT 1 NOT NULL;"))
                # Timetable performance indexes
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tt_entries_room_slot ON timetable_entries (timetable_version_id, room_id, time_slot_id);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tt_entries_version ON timetable_entries (timetable_version_id);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tt_entries_time_slot ON timetable_entries (time_slot_id);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tt_entries_subject ON timetable_entries (subject_id);"))
    except (RuntimeError, Exception) as ex:
        print(f"[ensure_database Warning] {ex}")


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
