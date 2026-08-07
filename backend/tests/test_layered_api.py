import os
import sys
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.core.database import get_db


@pytest.mark.asyncio
async def test_layered_architecture_faculty_endpoints(async_db_session):
    async def _override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. List Faculty
            res = await ac.get("/api/v1/configure/faculty")
            assert res.status_code == 200
            faculties = res.json()
            assert isinstance(faculties, list)

            # 2. Create Faculty
            new_fac = {
                "name": "Dr. Test Layered Professor",
                "employee_id": "VF-TEST-999",
                "designation": "Professor",
                "max_hours_per_week": 12,
                "max_daily_classes": 4
            }
            create_res = await ac.post("/api/v1/configure/faculty", json=new_fac)
            assert create_res.status_code == 201
            created_data = create_res.json()
            assert created_data["name"] == "Dr. Test Layered Professor"
            fac_id = created_data["id"]

            # 3. Update Faculty
            update_payload = {"max_hours_per_week": 14}
            update_res = await ac.put(f"/api/v1/configure/faculty/{fac_id}", json=update_payload)
            assert update_res.status_code == 200
            assert update_res.json()["max_hours_per_week"] == 14

            # 4. Delete Faculty
            del_res = await ac.delete(f"/api/v1/configure/faculty/{fac_id}")
            assert del_res.status_code == 204
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_layered_architecture_rooms_endpoints(async_db_session):
    async def _override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. List Rooms
            res = await ac.get("/api/v1/configure/rooms")
            assert res.status_code == 200
            rooms = res.json()
            assert isinstance(rooms, list)

            # 2. Create Room
            new_room = {
                "code": "TEST-101",
                "room_type": "gpu_lab",
                "capacity": 72,
                "gpu_capable": True
            }
            create_res = await ac.post("/api/v1/configure/rooms", json=new_room)
            assert create_res.status_code == 201
            created_data = create_res.json()
            assert created_data["code"] == "TEST-101"
            room_id = created_data["id"]

            # 3. Delete Room
            del_res = await ac.delete(f"/api/v1/configure/rooms/{room_id}")
            assert del_res.status_code == 204
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rfc7807_error_handler(async_db_session):
    async def _override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Fetch non-existent faculty ID
            res = await ac.delete("/api/v1/configure/faculty/999999")
            assert res.status_code == 404
            data = res.json()
            assert "code" in data
            assert data["code"] == "RESOURCE_NOT_FOUND"
            assert "timestamp" in data
    finally:
        app.dependency_overrides.clear()
