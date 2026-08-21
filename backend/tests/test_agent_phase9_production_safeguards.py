import pytest
from httpx import AsyncClient, ASGITransport
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.core.database import ensure_database, AsyncSessionLocal
from app.services.timetable_service import TimetableService


@pytest.mark.asyncio
async def test_phase9_data_integrity_health_and_rate_limiting():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test GET /api/v1/agent/health/data-integrity
        h_res = await client.get("/api/v1/agent/health/data-integrity")
        assert h_res.status_code == 200
        data = h_res.json()
        assert "status" in data
        assert "room_resolution_pct" in data

        # Test simulation rate limiting
        s_res = await client.post(
            "/api/v1/agent/sessions",
            json={"goal": "Test Phase 9 simulation rate limiting"},
        )
        assert s_res.status_code == 200
        session_id = s_res.json()["id"]

        # First call succeeds
        c1 = await client.post(
            "/api/v1/agent/simulate/room_failure",
            json={"session_id": session_id, "room_code": "604"}
        )
        assert c1.status_code == 200

        # Rapid second call triggers 429 rate limit
        c2 = await client.post(
            "/api/v1/agent/simulate/room_failure",
            json={"session_id": session_id, "room_code": "604"}
        )
        assert c2.status_code == 429
