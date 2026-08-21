import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import AgentSession, AgentEvent, AgentAction, AgentDecision
from app.models.timetable import TimetableVersion, TimetableEntry
from app.models.room import Room
from app.models.section import Section
from app.models.faculty import Faculty
from app.services.timetable_service import TimetableService
from backend.solver.conflict_checker import ConflictChecker


class ToolRegistry:
    """
    Central Tool Registry for the Autonomous Timetable Agent.
    Provides structured, auditable tool primitives for perception, analysis, repair, validation, and action.
    """

    @staticmethod
    async def log_action(
        db: AsyncSession,
        session_id: int,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        execution_time_ms: int,
        status: str = "success"
    ) -> AgentAction:
        """Persists a tool execution record to agent_actions audit table."""
        action = AgentAction(
            session_id=session_id,
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            status=status,
            execution_time_ms=execution_time_ms
        )
        db.add(action)
        await db.commit()
        await db.refresh(action)
        return action

    @staticmethod
    async def get_current_timetable(db: AsyncSession, version_id: int = 5) -> Dict[str, Any]:
        """Fetch the full current timetable entries and summary metrics."""
        start = time.time()
        res = await TimetableService.get_version_timetable(db, version_id=version_id, section_name="ALL")
        elapsed = int((time.time() - start) * 1000)
        return {
            "version_id": version_id,
            "count": res.get("count", 0),
            "entries": res.get("entries", []),
            "execution_time_ms": elapsed
        }

    @staticmethod
    async def get_rooms(db: AsyncSession) -> List[Dict[str, Any]]:
        """Fetch list of all active campus rooms and capacity attributes."""
        res = await db.execute(select(Room))
        rooms = res.scalars().all()
        if not rooms:
            from app.core.seed_cache import get_seed_data
            return get_seed_data().get("rooms", [])
        return [
            {
                "id": r.id,
                "code": r.code,
                "room_type": r.room_type,
                "capacity": r.capacity,
                "building_block": r.building_block
            }
            for r in rooms
        ]

    @staticmethod
    async def get_sections(db: AsyncSession) -> List[Dict[str, Any]]:
        """Fetch list of all department academic sections."""
        res = await db.execute(select(Section))
        secs = res.scalars().all()
        if not secs:
            from app.core.seed_cache import get_seed_data
            return get_seed_data().get("sections", [])
        return [
            {
                "id": s.id,
                "name": s.name,
                "student_count": s.student_count,
                "year_level": s.year_level
            }
            for s in secs
        ]

    @staticmethod
    async def get_faculty(db: AsyncSession) -> List[Dict[str, Any]]:
        """Fetch list of all teaching faculty members."""
        res = await db.execute(select(Faculty))
        facs = res.scalars().all()
        if not facs:
            from app.core.seed_cache import get_seed_data
            return get_seed_data().get("faculty", [])
        return [
            {
                "id": f.id,
                "name": f.name,
                "designation": f.designation,
                "max_hours_per_week": f.max_hours_per_week
            }
            for f in facs
        ]

    @staticmethod
    async def get_active_incidents(db: AsyncSession, session_id: int) -> List[Dict[str, Any]]:
        """Fetch unhandled disruption events associated with an active agent session."""
        res = await db.execute(
            select(AgentEvent)
            .where(AgentEvent.session_id == session_id)
            .order_by(AgentEvent.created_at.desc())
        )
        events = res.scalars().all()
        return [
            {
                "id": e.id,
                "event_type": e.event_type,
                "source": e.source,
                "severity": e.severity,
                "room_code": e.room_code,
                "affected_sections": e.affected_sections or [],
                "summary": e.summary,
                "payload": e.payload or {}
            }
            for e in events
        ]

    @staticmethod
    async def detect_conflicts(db: AsyncSession, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs ground-truth incremental conflict detection over target timetable entries."""
        checker = ConflictChecker()
        report = checker.detect(entries)
        hard_count = report.total_hard_violations
        return {
            "hard_violations": hard_count,
            "room_clashes": report.room_clashes,
            "faculty_clashes": report.faculty_clashes,
            "student_clashes": report.student_clashes,
            "break_clashes": report.break_clashes,
            "soft_violations": 0,
            "has_clashes": hard_count > 0,
            "details": [d.__dict__ if hasattr(d, "__dict__") else str(d) for d in report.details]
        }

    @staticmethod
    async def calculate_disruption_metrics(
        original_entries: List[Dict[str, Any]],
        repaired_entries: List[Dict[str, Any]],
        target_room_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculates quantitative schedule stability metrics between baseline and candidate repair."""
        orig_map = {str(e.get("id", "")): e for e in original_entries if e.get("id")}
        rep_map = {str(e.get("id", "")): e for e in repaired_entries if e.get("id")}

        moved_count = 0
        displaced_sections = set()
        displaced_faculty = set()

        for eid, rep_e in rep_map.items():
            orig_e = orig_map.get(eid)
            if not orig_e:
                continue
            orig_room = str(orig_e.get("room", "")).strip().upper()
            rep_room = str(rep_e.get("room", "")).strip().upper()
            orig_ts = f"{orig_e.get('day')}_{orig_e.get('period')}"
            rep_ts = f"{rep_e.get('day')}_{rep_e.get('period')}"

            if orig_room != rep_room or orig_ts != rep_ts:
                moved_count += 1
                if orig_e.get("section"):
                    displaced_sections.add(str(orig_e.get("section")))
                if orig_e.get("faculty"):
                    facs = orig_e.get("faculty")
                    if isinstance(facs, list):
                        for f in facs:
                            displaced_faculty.add(str(f))
                    else:
                        displaced_faculty.add(str(facs))

        total_entries = max(len(original_entries), 1)
        stability_score = round(max(0.0, 100.0 - ((moved_count / total_entries) * 100.0)), 1)
        risk_level = "low" if moved_count <= 2 else ("medium" if moved_count <= 6 else "high")

        return {
            "moved_entries": moved_count,
            "displaced_sections": sorted(list(displaced_sections)),
            "displaced_faculty": sorted(list(displaced_faculty)),
            "stability_score": stability_score,
            "risk_level": risk_level
        }

    @staticmethod
    async def save_schedule_snapshot(
        db: AsyncSession,
        session_id: int,
        entries: List[Dict[str, Any]],
        label: str = "snapshot"
    ) -> Dict[str, Any]:
        """Saves current schedule payload into agent session context snapshot memory."""
        res = await db.execute(select(AgentSession).where(AgentSession.id == session_id))
        session = res.scalar_one_or_none()
        if not session:
            raise ValueError(f"Agent session {session_id} not found")

        ctx = session.context or {}
        snapshots = ctx.get("snapshots", {})
        snapshots[label] = {
            "entries": entries,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        session.context = {**ctx, "snapshots": snapshots}
        await db.commit()
        return {"session_id": session_id, "snapshot": label, "count": len(entries)}

    @staticmethod
    async def rollback_schedule(db: AsyncSession, session_id: int) -> Dict[str, Any]:
        """Restores exact pre-disruption timetable snapshot if available."""
        res = await db.execute(select(AgentSession).where(AgentSession.id == session_id))
        session = res.scalar_one_or_none()
        if not session:
            raise ValueError(f"Agent session {session_id} not found")

        ctx = session.context or {}
        snapshots = ctx.get("snapshots", {})
        pre_snapshot = snapshots.get("pre_incident") or snapshots.get("initial")

        if not pre_snapshot or not pre_snapshot.get("entries"):
            # Fallback to standard V5 timetable entries
            v5_data = await TimetableService.get_version_timetable(db, version_id=5, section_name="ALL")
            restored_entries = v5_data.get("entries", [])
        else:
            restored_entries = pre_snapshot.get("entries", [])

        session.current_step = "observe"
        session.status = "active"
        session.summary = "Schedule rolled back to pre-incident snapshot."
        session.context = {
            **ctx,
            "last_event": "ROLLBACK",
            "active_repair": None
        }
        await db.commit()

        # Log action to audit trail
        action = AgentAction(
            session_id=session_id,
            tool_name="rollback_schedule",
            arguments={"snapshot_used": "pre_incident" if pre_snapshot else "v5_baseline"},
            result={"restored_count": len(restored_entries)},
            status="success",
            execution_time_ms=10
        )
        db.add(action)
        await db.commit()

        return {
            "session_id": session_id,
            "status": "rolled_back",
            "restored_entries_count": len(restored_entries),
            "entries": restored_entries
        }

    @staticmethod
    async def run_local_repair(
        db: AsyncSession,
        session_id: int,
        room_code: Optional[str] = None,
        faculty_name: Optional[str] = None,
        affected_sections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Runs minimal-disruption local repair using CP-SAT constraint logic."""
        start_time = time.time()
        tt_data = await ToolRegistry.get_current_timetable(db)
        original_entries = tt_data.get("entries", [])
        rooms = await ToolRegistry.get_rooms(db)

        from backend.solver.csat_solver import CPSATSolver
        solver = CPSATSolver()
        repair_res = solver.solve_local_repair(
            current_entries=original_entries,
            available_rooms=rooms,
            disrupted_room_code=room_code,
            disrupted_faculty_name=faculty_name
        )

        repaired_entries = repair_res.get("entries", [])
        validation = await ToolRegistry.detect_conflicts(db, repaired_entries)
        metrics = await ToolRegistry.calculate_disruption_metrics(original_entries, repaired_entries, target_room_code=room_code)

        elapsed_ms = int((time.time() - start_time) * 1000)
        result = {
            "status": repair_res.get("status", "OPTIMAL"),
            "moved_count": metrics["moved_entries"],
            "displaced_sections": metrics["displaced_sections"],
            "displaced_faculty": metrics["displaced_faculty"],
            "stability_score": metrics["stability_score"],
            "risk_level": metrics["risk_level"],
            "hard_violations": validation["hard_violations"],
            "has_clashes": validation["has_clashes"],
            "entries": repaired_entries,
            "execution_time_ms": elapsed_ms
        }

        # Save candidate repair snapshot
        await ToolRegistry.save_schedule_snapshot(db, session_id, repaired_entries, label="candidate_repair")

        # Audit log
        await ToolRegistry.log_action(
            db,
            session_id=session_id,
            tool_name="run_local_repair",
            arguments={"room_code": room_code, "faculty_name": faculty_name, "affected_sections": affected_sections or []},
            result=result,
            execution_time_ms=elapsed_ms
        )

        return result
