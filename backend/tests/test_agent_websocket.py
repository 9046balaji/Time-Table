import pytest
from fastapi.testclient import TestClient
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.services.agent_websocket_manager import agent_ws_manager


def test_agent_websocket_manager_broadcast():
    client = TestClient(app)
    session_id = 999

    with client.websocket_connect(f"/api/v1/agent/stream/{session_id}") as websocket:
        # Test ping-pong
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert data == "pong"

        # Verify broadcast
        import asyncio
        asyncio.run(agent_ws_manager.broadcast_event(session_id, {"type": "TEST_EVENT", "payload": "hello"}))
        msg = websocket.receive_json()
        assert msg["type"] == "TEST_EVENT"
        assert msg["payload"] == "hello"
