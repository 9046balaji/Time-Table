from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import ensure_database
from app.models.agent import AgentEvent, AgentSession


class AgentService:
    @staticmethod
    def _serialize_datetime(value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _serialize_session(session: AgentSession) -> Dict[str, Any]:
        return {
            "id": session.id,
            "goal": session.goal,
            "status": session.status,
            "current_step": session.current_step,
            "priority": session.priority or [],
            "summary": session.summary,
            "context": session.context or {},
            "created_at": AgentService._serialize_datetime(session.created_at),
            "updated_at": AgentService._serialize_datetime(session.updated_at),
        }

    @staticmethod
    def _serialize_event(event: AgentEvent) -> Dict[str, Any]:
        return {
            "id": event.id,
            "session_id": event.session_id,
            "event_type": event.event_type,
            "source": event.source,
            "severity": event.severity,
            "room_code": event.room_code,
            "affected_sections": event.affected_sections or [],
            "summary": event.summary,
            "payload": event.payload or {},
            "created_at": AgentService._serialize_datetime(event.created_at),
        }

    @staticmethod
    async def create_session(db: AsyncSession, goal: str, priority: Optional[List[str]] = None) -> Dict[str, Any]:
        await ensure_database()
        priorities = list(priority or [])
        session = AgentSession(
            goal=goal,
            status="active",
            current_step="observe",
            priority=priorities,
            summary=f"Mission started: {goal}",
            context={"goal": goal, "priority": priorities},
        )
        db.add(session)
        await db.flush()

        session_event = AgentEvent(
            session_id=session.id,
            event_type="MISSION_STARTED",
            source="user",
            severity="low",
            summary=f"Agent mission started for: {goal}",
            payload={"goal": goal, "priority": priorities},
            affected_sections=[],
        )
        db.add(session_event)
        await db.commit()
        await db.refresh(session)

        return AgentService._serialize_session(session)

    @staticmethod
    async def get_session(db: AsyncSession, session_id: int) -> Dict[str, Any]:
        await ensure_database()
        result = await db.execute(
            select(AgentSession).where(AgentSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        event_result = await db.execute(
            select(AgentEvent)
            .where(AgentEvent.session_id == session_id)
            .order_by(AgentEvent.created_at.asc())
        )
        events = event_result.scalars().all()
        payload = AgentService._serialize_session(session)
        payload["events"] = [AgentService._serialize_event(e) for e in events]
        return payload

    @staticmethod
    async def simulate_room_failure(
        db: AsyncSession,
        session_id: int,
        room_code: str,
        severity: str = "high",
        affected_sections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        await ensure_database()
        result = await db.execute(select(AgentSession).where(AgentSession.id == session_id))
        session = result.scalar_one_or_none()
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        sections = list(affected_sections or [])
        summary = (
            f"Room {room_code} is unavailable; agent recommends a local repair for {len(sections) or 'the affected'} "
            f"section(s)."
        )

        event = AgentEvent(
            session_id=session.id,
            event_type="ROOM_UNAVAILABLE",
            source="simulation",
            severity=severity,
            room_code=room_code,
            affected_sections=sections,
            summary=summary,
            payload={
                "room_code": room_code,
                "severity": severity,
                "affected_sections": sections,
                "recommendation": "local_repair",
            },
        )
        db.add(event)

        session.current_step = "repair"
        session.status = "active"
        session.summary = summary
        session.context = {
            **(session.context or {}),
            "last_event": "ROOM_UNAVAILABLE",
            "last_room": room_code,
            "affected_sections": sections,
        }
        await db.commit()
        await db.refresh(event)

        return {
            "id": event.id,
            "session_id": session.id,
            "event_type": event.event_type,
            "source": event.source,
            "severity": event.severity,
            "room_code": event.room_code,
            "affected_sections": event.affected_sections or [],
            "summary": event.summary,
            "payload": event.payload or {},
            "created_at": AgentService._serialize_datetime(event.created_at),
        }
