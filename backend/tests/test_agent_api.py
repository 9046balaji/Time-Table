import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_create_agent_session_and_room_failure_event():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        session_response = await client.post(
            "/api/v1/agent/sessions",
            json={
                "goal": "Repair timetable after room outage",
                "priority": ["final_year", "hard_constraints"],
            },
        )
        assert session_response.status_code == 200, session_response.text
        session_data = session_response.json()
        assert session_data["goal"] == "Repair timetable after room outage"
        assert "id" in session_data

        event_response = await client.post(
            "/api/v1/agent/simulate-room-failure",
            json={
                "session_id": session_data["id"],
                "room_code": "AFTF-12",
                "severity": "high",
                "affected_sections": ["III AIML-A", "III AIML-B"],
            },
        )
        assert event_response.status_code == 200, event_response.text
        data = event_response.json()
        assert data["event_type"] == "ROOM_UNAVAILABLE"
        assert data["severity"] == "high"
        assert data["room_code"] == "AFTF-12"
        assert data["affected_sections"] == ["III AIML-A", "III AIML-B"]
        assert "summary" in data

        repair_response = await client.post(
            f"/api/v1/agent/sessions/{session_data['id']}/repair-suggestion",
            json={
                "room_code": "AFTF-12",
                "affected_sections": ["III AIML-A", "III AIML-B"],
                "proposed_room": "604",
                "risk_level": "medium",
                "reason": "Shift affected labs to the nearest available classroom-lab block.",
            },
        )
        assert repair_response.status_code == 200, repair_response.text
        repair_data = repair_response.json()
        assert repair_data["event_type"] == "REPAIR_SUGGESTED"
        assert repair_data["payload"]["proposed_room"] == "604"
        assert repair_data["payload"]["risk_level"] == "medium"

        decision_response = await client.post(
            f"/api/v1/agent/sessions/{session_data['id']}/repair-decision",
            json={
                "decision": "approved",
                "rationale": "The swap keeps all critical labs in the same teaching block.",
            },
        )
        assert decision_response.status_code == 200, decision_response.text
        decision_data = decision_response.json()
        assert decision_data["event_type"] == "REPAIR_DECISION"
        assert decision_data["payload"]["decision"] == "approved"
        assert decision_data["payload"]["session_id"] == session_data["id"]
