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
