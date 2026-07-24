import pytest
import os
import sys
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import get_db
from main import app


@pytest.mark.asyncio
async def test_configure_endpoints_with_session(async_db_session):
    async def _override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = _override_get_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Test List Faculty
            res = await client.get("/api/v1/configure/faculty")
            assert res.status_code == 200
            assert isinstance(res.json(), list)

            # 2. Test List Rooms
            res = await client.get("/api/v1/configure/rooms")
            assert res.status_code == 200
            assert isinstance(res.json(), list)

            # 3. Test List Subjects
            res = await client.get("/api/v1/configure/subjects")
            assert res.status_code == 200
            assert isinstance(res.json(), list)

            # 4. Test CSV Import Rooms
            csv_content = "code,room_type,capacity,floor,block,gpu_capable\nTEST-101,classroom,60,6,U-Block,false\nTEST-102,gpu_lab,70,AFTF,U-Block,true\n"
            files = {"file": ("rooms.csv", csv_content.encode("utf-8"), "text/csv")}
            res = await client.post("/api/v1/configure/import-csv?entity_type=rooms", files=files)
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["imported_count"] == 2

    finally:
        app.dependency_overrides.clear()
