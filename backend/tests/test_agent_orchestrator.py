import pytest
from httpx import AsyncClient, ASGITransport
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.services.tool_registry import ToolRegistry


@pytest.mark.asyncio
async def test_tool_registry_disruption_metrics():
    orig_entries = [
        {"id": "1", "section": "II AIML-A", "day": "MON", "period": 1, "room": "604", "faculty": "Dr. Reddy"},
        {"id": "2", "section": "II AIML-B", "day": "MON", "period": 2, "room": "604", "faculty": "P. Girija"},
    ]
    rep_entries = [
        {"id": "1", "section": "II AIML-A", "day": "MON", "period": 1, "room": "605", "faculty": "Dr. Reddy"},  # Room changed
        {"id": "2", "section": "II AIML-B", "day": "MON", "period": 2, "room": "604", "faculty": "P. Girija"},  # Same
    ]

    metrics = await ToolRegistry.calculate_disruption_metrics(orig_entries, rep_entries)
    assert metrics["moved_entries"] == 1
    assert "II AIML-A" in metrics["displaced_sections"]
    assert metrics["risk_level"] == "low"


@pytest.mark.asyncio
async def test_agent_orchestrator_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Session
        res = await client.post(
            "/api/v1/agent/sessions",
            json={"goal": "Test agent orchestration lifecycle", "priority": ["hard_constraints"]},
        )
        assert res.status_code == 200
        session_data = res.json()
        session_id = session_data["id"]
        assert session_data["status"] == "active"
        assert session_data["current_step"] == "observe"

        # 2. Observe State
        obs_res = await client.post(f"/api/v1/agent/sessions/{session_id}/observe")
        assert obs_res.status_code == 200
        obs_data = obs_res.json()
        assert obs_data["session_id"] == session_id
        assert obs_data["entries_count"] >= 0

        # 3. Simulate Room Failure
        sim_res = await client.post(
            "/api/v1/agent/simulate-room-failure",
            json={
                "session_id": session_id,
                "room_code": "604",
                "severity": "high",
                "affected_sections": ["III AIML-A", "III AIML-B"],
            },
        )
        assert sim_res.status_code == 200
        sim_data = sim_res.json()
        assert sim_data["event_type"] == "ROOM_UNAVAILABLE"
        assert sim_data["room_code"] == "604"

        # 4. Rollback Schedule
        rb_res = await client.post(f"/api/v1/agent/sessions/{session_id}/rollback")
        assert rb_res.status_code == 200
        rb_data = rb_res.json()
        assert rb_data["session_id"] == session_id
        assert rb_data["status"] == "rolled_back"
