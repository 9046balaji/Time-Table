import asyncio
import json
from typing import Dict, Set, Any
from fastapi import WebSocket


class AgentWebSocketManager:
    """
    Real-Time WebSocket Connection & Event Broadcast Manager.
    Streams live decision traces, solver progress, and incident notifications to active agent console clients.
    """

    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, session_id: int, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)

    def disconnect(self, session_id: int, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast_event(self, session_id: int, message: Dict[str, Any]):
        """Broadcasts a JSON event payload to all connected listeners for a given session_id."""
        if session_id not in self.active_connections:
            return

        dead_sockets = set()
        for websocket in list(self.active_connections[session_id]):
            try:
                await websocket.send_json(message)
            except Exception:
                dead_sockets.add(websocket)

        for ws in dead_sockets:
            self.disconnect(session_id, ws)


# Global singleton manager instance
agent_ws_manager = AgentWebSocketManager()
