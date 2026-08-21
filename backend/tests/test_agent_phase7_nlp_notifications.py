import pytest
from httpx import AsyncClient, ASGITransport
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.core.database import ensure_database, AsyncSessionLocal
from app.services.tool_registry import ToolRegistry


@pytest.mark.asyncio
async def test_phase7_nlp_command_and_notifications():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create session
        res = await client.post(
            "/api/v1/agent/sessions",
            json={"goal": "Test Phase 7 natural language parsing and notifications"},
        )
        assert res.status_code == 200
        session_id = res.json()["id"]

        # Parse natural command
        nlp_res = await client.post(
            f"/api/v1/agent/sessions/{session_id}/parse-command",
            json={"command": "Emergency maintenance in Lab 604 Monday"}
        )
        assert nlp_res.status_code == 200
        data = nlp_res.json()
        assert data["scenario"] == "room_failure"
        assert data["target"] == "604"

        # Test send_notification tool
        await ensure_database()
        async with AsyncSessionLocal() as db:
            notif = await ToolRegistry.send_notification(
                db,
                session_id=session_id,
                recipients=["head_acse@vignan.ac.in", "student_rep_3a@vignan.ac.in"],
                channel="email_push",
                message="Lab 604 maintenance re-routed to Lab 605."
            )
            assert notif["delivered_count"] == 2
            assert notif["channel"] == "email_push"
