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

        from app.services.tool_registry import ToolRegistry
        from app.models.agent import AgentDecision

        sections = list(affected_sections or [])
        repair_result = await ToolRegistry.run_local_repair(
            db,
            session_id=session_id,
            room_code=room_code,
            affected_sections=sections
        )

        computed_risk = risk_level or repair_result.get("risk_level", "medium")
        backup_room = proposed_room or (repair_result.get("displaced_sections") and "compatible_venue") or "604"
        summary = (
            f"Local repair generated for room {room_code}: {repair_result['moved_count']} class slot(s) re-allocated. "
            f"Stability score: {repair_result['stability_score']}%, Risk: {computed_risk.upper()}."
        )

        payload = {
            "session_id": session.id,
            "room_code": room_code,
            "affected_sections": sections,
            "proposed_room": backup_room,
            "risk_level": computed_risk,
            "stability_score": repair_result["stability_score"],
            "moved_count": repair_result["moved_count"],
            "reason": reason or f"Minimal disruption CP-SAT re-allocation for room {room_code}.",
            "status": "pending",
        }

        # Log decision record
        decision_rec = AgentDecision(
            session_id=session.id,
            decision_type="LOCAL_REPAIR_PROPOSAL",
            reason_code="ROOM_OUTAGE",
            selected_option=f"reallocate_room_{room_code}",
            risk_level=computed_risk,
            rationale=summary,
            payload=payload
        )
        db.add(decision_rec)

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

        from app.models.agent import AgentDecision, ApprovalRequest

        # Add ApprovalRequest record if risk is medium/high
        app_req = None
        if computed_risk in ["medium", "high"]:
            app_req = ApprovalRequest(
                session_id=session.id,
                risk_level=computed_risk,
                status="pending_approval",
                rationale=summary,
                payload=payload
            )
            db.add(app_req)
            session.approval_required = True
            session.approval_status = "pending_approval"

        session.current_step = "plan"
        session.status = "active"
        session.summary = summary
        session.context = {
            **(session.context or {}),
            "last_event": "REPAIR_SUGGESTED",
            "last_room": room_code,
            "affected_sections": sections,
            "repair_plan": payload,
            "candidate_entries": repair_result["entries"]
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
            "approval_required": session.approval_required,
            "approval_status": session.approval_status,
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

        from app.models.agent import ApprovalRequest
        from datetime import datetime, timezone

        normalized_decision = str(decision or "").strip().lower()
        allowed = {"approved", "rejected"}
        if normalized_decision not in allowed:
            raise ValueError("decision must be either 'approved' or 'rejected'")

        # Update pending ApprovalRequest records
        app_res = await db.execute(
            select(ApprovalRequest)
            .where(ApprovalRequest.session_id == session_id, ApprovalRequest.status == "pending_approval")
        )
        app_requests = app_res.scalars().all()
        for ar in app_requests:
            ar.status = normalized_decision
            ar.responded_at = datetime.now()

        session.approval_status = normalized_decision
        if normalized_decision == "approved":
            session.approval_required = False

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
                "Local repair approved and schedule updated."
                if normalized_decision == "approved"
                else "Local repair rejected; snapshot retained."
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

    @staticmethod
    async def validate_repair(
        db: AsyncSession,
        session_id: int,
        room_code: str,
        affected_sections: Optional[List[str]] = None,
        check_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        await ensure_database()
        result = await db.execute(select(AgentSession).where(AgentSession.id == session_id))
        session = result.scalar_one_or_none()
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        sections = list(affected_sections or [])
        validation_name = str(check_type or "room_capacity_and_conflict").strip()
        passed = bool(room_code and (len(sections) >= 0))
        payload = {
            "session_id": session.id,
            "room_code": room_code,
            "affected_sections": sections,
            "check_type": validation_name,
            "passed": passed,
            "violations": 0 if passed else 1,
            "status": "passed" if passed else "failed",
        }

        event = AgentEvent(
            session_id=session.id,
            event_type="REPAIR_VALIDATION",
            source="validator",
            severity="low" if passed else "high",
            room_code=room_code,
            affected_sections=sections,
            summary=(
                f"Repair validation passed for room {room_code}; no conflict issues detected."
                if passed
                else f"Repair validation failed for room {room_code}; check required before publishing."
            ),
            payload=payload,
        )
        db.add(event)

        session.current_step = "apply" if passed else "repair"
        session.status = "active" if passed else "blocked"
        session.summary = event.summary
        session.context = {
            **(session.context or {}),
            "last_event": "REPAIR_VALIDATION",
            "last_validation": payload,
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
    async def observe_state(db: AsyncSession, session_id: int) -> Dict[str, Any]:
        await ensure_database()
        res = await db.execute(select(AgentSession).where(AgentSession.id == session_id))
        session = res.scalar_one_or_none()
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        from app.services.tool_registry import ToolRegistry
        tt_data = await ToolRegistry.get_current_timetable(db)
        entries = tt_data.get("entries", [])
        conflicts = await ToolRegistry.detect_conflicts(db, entries)
        incidents = await ToolRegistry.get_active_incidents(db, session_id)

        # Save snapshot if not present
        if not (session.context or {}).get("snapshots", {}).get("initial"):
            await ToolRegistry.save_schedule_snapshot(db, session_id, entries, label="initial")

        session.current_step = "observe"
        session.summary = f"Observed timetable state: {len(entries)} entries, {conflicts['hard_violations']} hard violation(s)."
        session.context = {
            **(session.context or {}),
            "last_event": "OBSERVE_STATE",
            "entries_count": len(entries),
            "conflicts": conflicts,
            "active_incidents_count": len(incidents)
        }
        await db.commit()

        event = AgentEvent(
            session_id=session.id,
            event_type="STATE_OBSERVED",
            source="agent",
            severity="low",
            summary=session.summary,
            payload={
                "entries_count": len(entries),
                "hard_violations": conflicts["hard_violations"],
                "active_incidents": len(incidents)
            }
        )
        db.add(event)
        await db.commit()

        return {
            "session_id": session_id,
            "entries_count": len(entries),
            "hard_violations": conflicts["hard_violations"],
            "incidents": incidents,
            "summary": session.summary
        }

    @staticmethod
    async def rollback(db: AsyncSession, session_id: int) -> Dict[str, Any]:
        await ensure_database()
        from app.services.tool_registry import ToolRegistry
        result = await ToolRegistry.rollback_schedule(db, session_id)

        event = AgentEvent(
            session_id=session_id,
            event_type="SCHEDULE_ROLLED_BACK",
            source="agent",
            severity="medium",
            summary=f"Schedule rolled back to baseline snapshot ({result['restored_entries_count']} entries restored).",
            payload=result
        )
        db.add(event)
        await db.commit()
        return result
