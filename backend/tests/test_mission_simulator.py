import pytest
from httpx import AsyncClient, ASGITransport
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app


@pytest.mark.asyncio
async def test_mission_simulator_all_scenarios():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create Session
        res = await client.post(
            "/api/v1/agent/sessions",
            json={"goal": "Test mission simulator scenarios", "priority": ["hard_constraints"]},
        )
        assert res.status_code == 200
        session_id = res.json()["id"]

        # 1. Room Failure
        rf_res = await client.post(
            "/api/v1/agent/simulate/room_failure",
            json={"session_id": session_id, "target_code": "604", "affected_sections": ["II AIML-A"]},
        )
        assert rf_res.status_code == 200
        rf_data = rf_res.json()
        assert rf_data["scenario"] == "room_failure"
        assert rf_data["event_type"] == "ROOM_UNAVAILABLE"
        assert "repair_recommendation" in rf_data

        # 2. Faculty Absence
        fa_res = await client.post(
            "/api/v1/agent/simulate/faculty_absence",
            json={"session_id": session_id, "target_code": "Dr. S. Srikantha Reddy"},
        )
        assert fa_res.status_code == 200
        fa_data = fa_res.json()
        assert fa_data["scenario"] == "faculty_absence"
        assert fa_data["event_type"] == "FACULTY_UNAVAILABLE"

        # 3. Capacity Surge
        cs_res = await client.post(
            "/api/v1/agent/simulate/capacity_surge",
            json={"session_id": session_id, "target_code": "601", "extra": {"new_student_count": 95}},
        )
        assert cs_res.status_code == 200
        assert cs_res.json()["scenario"] == "capacity_surge"

        # 4. Priority Reroute
        pr_res = await client.post(
            "/api/v1/agent/simulate/priority_reroute",
            json={"session_id": session_id, "target_code": "IV AIML-A"},
        )
        assert pr_res.status_code == 200
        assert pr_res.json()["scenario"] == "priority_reroute"

        # 5. Constraint Adjustment
        ca_res = await client.post(
            "/api/v1/agent/simulate/constraint_adjustment",
            json={"session_id": session_id, "target_code": "HC-08"},
        )
        assert ca_res.status_code == 200
        assert ca_res.json()["scenario"] == "constraint_adjustment"
