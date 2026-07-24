import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "VFSTR" in data["project"]


@pytest.mark.asyncio
async def test_list_sections_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/sections")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 40
        assert any(s["name"] == "II AIML-A" for s in data["items"])


@pytest.mark.asyncio
async def test_list_faculty_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/faculty")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["count"] > 0
        assert any(f["name"] == "Dr. P. Kalpana" for f in data["items"])


@pytest.mark.asyncio
async def test_list_rooms_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/rooms?type=classroom")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert all(r["type"] == "classroom" for r in data["items"])


@pytest.mark.asyncio
async def test_validate_timetable_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/validate/5")
        assert response.status_code == 200
        data = response.json()
        assert data["version_id"] == 5
        assert data["hard_violations"] == 51
        assert data["status"] == "NEEDS_FIX"


@pytest.mark.asyncio
async def test_trigger_solver_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"algorithm": "CP-SAT", "timeout_seconds": 30}
        response = await client.post("/api/v1/solve", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["status"] == "RUNNING"
