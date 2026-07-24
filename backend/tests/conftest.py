import sys
import os

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import BaseModel
from app.models import Department, AcademicYear, Branch, Section, Faculty, Room, Subject, TimeSlot


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def async_test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_db_session(async_test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(async_test_engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session
