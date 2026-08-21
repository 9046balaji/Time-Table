import pytest
from httpx import AsyncClient, ASGITransport
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app


@pytest.mark.asyncio
async def test_phase2_dynamic_consensus_and_approval_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create session
        res = await client.post(
            "/api/v1/agent/sessions",
            json={"goal": "Test Phase 2 dynamic consensus and approval gate"},
        )
        assert res.status_code == 200
        session_id = res.json()["id"]

        # Trigger room failure
        rf_res = await client.post(
            "/api/v1/agent/simulate/room_failure",
            json={"session_id": session_id, "target_code": "604", "affected_sections": ["II AIML-A"]},
        )
        assert rf_res.status_code == 200

        # Request repair suggestion
        sug_res = await client.post(
            f"/api/v1/agent/sessions/{session_id}/repair-suggestion",
            json={"room_code": "604", "affected_sections": ["II AIML-A"], "risk_level": "high"},
        )
        assert sug_res.status_code == 200
        sug_data = sug_res.json()
        assert sug_data["approval_required"] is True
        assert sug_data["approval_status"] == "pending_approval"

        # Dynamic consensus check
        c_res = await client.post(
            f"/api/v1/agent/sessions/{session_id}/consensus",
            json={
                "entries": [
                    {"id": "1", "section": "II AIML-A", "day": "MON", "period": 1, "subject": "DS", "room": "601", "faculty": ["Dr. S. Srikantha Reddy"]}
                ]
            }
        )
        assert c_res.status_code == 200
        c_data = c_res.json()
        assert c_data["consensus_passed"] is True

        # Test POST /approve endpoint
        app_res = await client.post(
            f"/api/v1/agent/sessions/{session_id}/approve",
            json={"rationale": "Approved by academic coordinator"}
        )
        assert app_res.status_code == 200
        assert app_res.json()["payload"]["status"] == "approved"
