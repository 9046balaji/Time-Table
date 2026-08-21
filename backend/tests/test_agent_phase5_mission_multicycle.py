import pytest
from httpx import AsyncClient, ASGITransport
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app


@pytest.mark.asyncio
async def test_phase5_mission_simulator_multicycle_scenarios():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create session
        res = await client.post(
            "/api/v1/agent/sessions",
            json={"goal": "Test Phase 5 multi-cycle scenario simulation"},
        )
        assert res.status_code == 200
        session_id = res.json()["id"]

        # Cycle 1: Trigger M7 GPU Lab Failure scenario
        gpu_res = await client.post(
            "/api/v1/agent/simulate/gpu_lab_failure",
            json={"session_id": session_id, "target_code": "AFTF-12", "affected_sections": ["IV AIML-A"]}
        )
        assert gpu_res.status_code == 200
        gpu_data = gpu_res.json()
        assert gpu_data["scenario"] == "gpu_lab_failure"
        assert gpu_data["iteration"] >= 2

        # Cycle 2: Trigger Faculty Absence scenario sequentially on same session
        fac_res = await client.post(
            "/api/v1/agent/simulate/faculty_absence",
            json={"session_id": session_id, "target_code": "Dr. S. Srikantha Reddy", "affected_sections": ["II AIML-A"]}
        )
        assert fac_res.status_code == 200
        fac_data = fac_res.json()
        assert fac_data["scenario"] == "faculty_absence"
        assert fac_data["iteration"] >= 3
