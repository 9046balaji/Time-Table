import pytest
from httpx import AsyncClient, ASGITransport
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app


@pytest.mark.asyncio
async def test_multi_agent_consensus_evaluation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create Session
        res = await client.post(
            "/api/v1/agent/sessions",
            json={"goal": "Test multi agent consensus protocol", "priority": ["hard_constraints"]},
        )
        assert res.status_code == 200
        session_id = res.json()["id"]

        # Valid timetable entries mock
        mock_entries = [
            {
                "id": "e1",
                "section": "II AIML-A",
                "day": "MON",
                "period": 1,
                "subject": "DS",
                "room": "601",
                "faculty": ["Dr. S. Srikantha Reddy"]
            },
            {
                "id": "e2",
                "section": "II AIML-B",
                "day": "MON",
                "period": 2,
                "subject": "DBMS",
                "room": "602",
                "faculty": ["P. Girija"]
            }
        ]

        # Evaluate consensus
        c_res = await client.post(
            f"/api/v1/agent/sessions/{session_id}/consensus",
            json={"entries": mock_entries}
        )
        assert c_res.status_code == 200
        data = c_res.json()
        assert data["consensus_passed"] is True
        assert data["status"] == "APPROVED"
        assert len(data["votes"]) == 3
        roles = [v["role"] for v in data["votes"]]
        assert "VALIDATOR" in roles
        assert "ARCHITECT" in roles
        assert "SOLVER" in roles
