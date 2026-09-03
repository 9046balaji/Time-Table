import sys
import os

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Add the repository root so the `backend.*` absolute imports used across the
# solver, parser and agent modules resolve when tests run from the host.
repo_root = os.path.abspath(os.path.join(backend_path, ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import BaseModel
import app.models  # noqa: F401
from main import app
from app.core.database import get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="session")
def shared_test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    return engine

@pytest_asyncio.fixture
async def async_test_engine(shared_test_engine):
    async with shared_test_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield shared_test_engine
    async with shared_test_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)

@pytest_asyncio.fixture
async def async_db_session(async_test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(async_test_engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db_overrides(async_test_engine):
    """Automatically patch FastAPI database engine and get_db dependency override to use SQLite in-memory."""
    import app.core.database as db_mod
    session_factory = async_sessionmaker(async_test_engine, expire_on_commit=False, class_=AsyncSession)
    
    orig_engine = db_mod.engine
    orig_maker = db_mod._CURRENT_SESSION_MAKER
    
    db_mod.engine = async_test_engine
    db_mod._CURRENT_SESSION_MAKER = session_factory

    async def _mock_get_db():
        async with session_factory() as session:
            yield session

    async def _mock_ensure_db():
        async with async_test_engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)

    orig_ensure = db_mod.ensure_database
    db_mod.ensure_database = _mock_ensure_db
    app.dependency_overrides[get_db] = _mock_get_db

    try:
        from app.api.v1.agent import _last_simulation_times
        _last_simulation_times.clear()
    except Exception:
        pass

    yield

    try:
        from app.api.v1.agent import _last_simulation_times
        _last_simulation_times.clear()
    except Exception:
        pass

    app.dependency_overrides.pop(get_db, None)
    db_mod.engine = orig_engine
    db_mod._CURRENT_SESSION_MAKER = orig_maker
    db_mod.ensure_database = orig_ensure
