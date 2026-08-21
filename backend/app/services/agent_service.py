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

    @staticmethod
    async def create_repair_suggestion(
        db: AsyncSession,
        session_id: int,
        room_code: str,
        affected_sections: Optional[List[str]] = None,
        proposed_room: Optional[str] = None,
        risk_level: str = "medium",
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        await ensure_database()
        result = await db.execute(select(AgentSession).where(AgentSession.id == session_id))
        session = result.scalar_one_or_none()
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        sections = list(affected_sections or [])
        backup_room = (proposed_room or "nearest_available_lab").strip()
        summary = (
            f"Local repair suggested for room {room_code}: move {len(sections) or 'affected'} affected section(s) "
            f"to {backup_room} and freeze unaffected slots."
        )

        payload = {
            "session_id": session.id,
            "room_code": room_code,
            "affected_sections": sections,
            "proposed_room": backup_room,
            "risk_level": risk_level,
            "reason": reason or "Move the impacted sections to the nearest compatible room block.",
            "status": "pending",
        }

        event = AgentEvent(
            session_id=session.id,
            event_type="REPAIR_SUGGESTED",
            source="agent",
            severity="medium",
            room_code=room_code,
            affected_sections=sections,
            summary=summary,
            payload=payload,
        )
        db.add(event)

        session.current_step = "plan"
        session.status = "active"
        session.summary = summary
        session.context = {
            **(session.context or {}),
            "last_event": "REPAIR_SUGGESTED",
            "last_room": room_code,
            "affected_sections": sections,
            "repair_plan": payload,
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

    @staticmethod
    async def resolve_repair_decision(
        db: AsyncSession,
        session_id: int,
        decision: str,
        rationale: Optional[str] = None,
    ) -> Dict[str, Any]:
        await ensure_database()
        result = await db.execute(select(AgentSession).where(AgentSession.id == session_id))
        session = result.scalar_one_or_none()
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        normalized_decision = str(decision or "").strip().lower()
        allowed = {"approved", "rejected"}
        if normalized_decision not in allowed:
            raise ValueError("decision must be either 'approved' or 'rejected'")

        payload = {
            "session_id": session.id,
            "decision": normalized_decision,
            "rationale": rationale or "No rationale supplied.",
            "status": normalized_decision,
        }

        event = AgentEvent(
            session_id=session.id,
            event_type="REPAIR_DECISION",
            source="human",
            severity="low" if normalized_decision == "approved" else "medium",
            affected_sections=list((session.context or {}).get("affected_sections") or []),
            summary=(
                "Local repair approved and ready for validation."
                if normalized_decision == "approved"
                else "Local repair rejected; continue monitoring the affected room."
            ),
            payload=payload,
        )
        db.add(event)

        session.current_step = "validate" if normalized_decision == "approved" else "observe"
        session.status = "active" if normalized_decision == "approved" else "blocked"
        session.summary = event.summary
        session.context = {
            **(session.context or {}),
            "last_event": "REPAIR_DECISION",
            "last_decision": normalized_decision,
            "decision_rationale": payload["rationale"],
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
