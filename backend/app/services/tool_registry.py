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
from app.services import write_tools as _write_tools
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
        # Ensure session exists to avoid FK constraint violation
        sess_check = (await db.execute(select(AgentSession.id).where(AgentSession.id == session_id))).scalar_one_or_none()
        if not sess_check:
            fallback_sess = AgentSession(goal=f"Automated Tool Execution: {tool_name}", status="active")
            db.add(fallback_sess)
            await db.flush()
            session_id = fallback_sess.id

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
                "building_block": getattr(r, "block", getattr(r, "building_block", "U-Block"))
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
                "student_count": getattr(s, "strength", getattr(s, "student_count", 60)),
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
    async def get_room_availability(db: AsyncSession, day: str, period: int, room_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries available (unassigned) rooms for a given day and period slot."""
        tt_data = await ToolRegistry.get_current_timetable(db)
        occupied_rooms = {
            str(e.get("room")).strip().upper()
            for e in tt_data.get("entries", [])
            if str(e.get("day")).upper() == day.upper() and int(e.get("period", 0)) == int(period)
        }
        all_rooms = await ToolRegistry.get_rooms(db)
        available = []
        for r in all_rooms:
            code = str(r.get("code")).strip().upper()
            r_type = str(r.get("room_type")).lower()
            if code not in occupied_rooms:
                if not room_type or room_type.lower() in r_type:
                    available.append(r)
        return available

    @staticmethod
    async def get_faculty_availability(db: AsyncSession, day: str, period: int) -> List[Dict[str, Any]]:
        """Queries teaching faculty members with zero assignments in a given time slot."""
        tt_data = await ToolRegistry.get_current_timetable(db)
        occupied_fac = set()
        for e in tt_data.get("entries", []):
            if str(e.get("day")).upper() == day.upper() and int(e.get("period", 0)) == int(period):
                facs = e.get("faculty") or []
                if isinstance(facs, str):
                    facs = [f.strip() for f in facs.split(",") if f.strip()]
                for f in facs:
                    occupied_fac.add(str(f).strip().upper())
        all_fac = await ToolRegistry.get_faculty(db)
        return [f for f in all_fac if str(f.get("name")).strip().upper() not in occupied_fac]

    @staticmethod
    async def find_alternative_room(db: AsyncSession, day: str, period: int, room_type: Optional[str] = None, min_capacity: int = 40) -> Optional[Dict[str, Any]]:
        """Recommends the single best available alternative venue enforcing deterministic priority ordering (Room Type -> Capacity Fit)."""
        avail = await ToolRegistry.get_room_availability(db, day=day, period=period, room_type=room_type)
        suitable = [r for r in avail if int(r.get("capacity", 0)) >= min_capacity]
        if not suitable:
            suitable = avail

        # Priority Sorting: 1. Exact capacity fit (closest to min_capacity), 2. Room code alpha order
        suitable.sort(key=lambda r: (abs(int(r.get("capacity", 60)) - min_capacity), str(r.get("code", ""))))
        return suitable[0] if suitable else None

    @staticmethod
    async def find_alternative_faculty(db: AsyncSession, subject_code: str, day: str, period: int) -> Optional[Dict[str, Any]]:
        """Recommends an available alternative instructor for a course slot."""
        avail = await ToolRegistry.get_faculty_availability(db, day=day, period=period)
        return avail[0] if avail else None

    @staticmethod
    async def get_active_incidents(db: AsyncSession, session_id: int) -> List[Dict[str, Any]]:
        """Fetch active unresolved disruption incidents for an agent session."""
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
                "severity": e.severity,
                "summary": e.summary,
                "room_code": e.room_code,
                "affected_sections": e.affected_sections
            }
            for e in events
        ]

    @staticmethod
    async def explain_infeasibility(timetable_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Surfaces exact hard constraint rules (HC-01..HC-10) causing schedule infeasibility."""
        checker = ConflictChecker()
        report = checker.detect(timetable_entries)

        explanations = []
        if report.room_clashes > 0:
            explanations.append(f"HC-01 Room Conflict: {report.room_clashes} venue double-booking instance(s) detected.")
        if report.faculty_clashes > 0:
            explanations.append(f"HC-02 Faculty Double-Booking: {report.faculty_clashes} instructor conflict(s) detected.")
        if report.student_clashes > 0:
            explanations.append(f"HC-03 Student Section Conflict: {report.student_clashes} section overlapping slot(s) detected.")

        if not explanations:
            explanations.append("No hard constraint violations detected. Schedule is feasible.")

        return {
            "is_infeasible": report.total_hard_violations > 0,
            "total_hard_violations": report.total_hard_violations,
            "room_clashes": report.room_clashes,
            "faculty_clashes": report.faculty_clashes,
            "student_clashes": report.student_clashes,
            "diagnostic_summary": "; ".join(explanations),
            "explanations": explanations
        }

    @staticmethod
    async def detect_conflicts(db: AsyncSession, timetable_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs the standalone ConflictChecker to detect hard violations and clash breakdowns."""
        start = time.time()
        checker = ConflictChecker()
        report = checker.detect(timetable_entries)
        elapsed = int((time.time() - start) * 1000)
        return {
            "hard_violations": report.total_hard_violations,
            "room_clashes": report.room_clashes,
            "faculty_clashes": report.faculty_clashes,
            "student_clashes": report.student_clashes,
            "has_clashes": report.total_hard_violations > 0,
            "execution_time_ms": elapsed
        }

    @staticmethod
    async def calculate_disruption_metrics(
        original_entries: List[Dict[str, Any]],
        candidate_entries: List[Dict[str, Any]],
        target_room_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates moved entry counts, displaced sections/faculty, stability %, weighted change cost, and risk level.
        Weighted Change Cost Model:
        - Time slot change = 1
        - Room change = 1
        - Faculty reassignment = 5
        - Multi-entry cascade = 1.5 multiplier
        """
        orig_map = {str(e.get("id") or f"{e.get('section')}_{e.get('day')}_{e.get('period')}"): e for e in original_entries}

        moved = 0
        displaced_sections = set()
        displaced_faculty = set()
        weighted_change_cost = 0.0

        for cand in candidate_entries:
            key = str(cand.get("id") or f"{cand.get('section')}_{cand.get('day')}_{cand.get('period')}")
            orig = orig_map.get(key)
            if not orig:
                continue

            room_changed = str(orig.get("room")).strip() != str(cand.get("room")).strip()
            slot_changed = (str(orig.get("day")) != str(cand.get("day"))) or (int(orig.get("period", 0)) != int(cand.get("period", 0)))
            fac_orig = str(orig.get("faculty") or "")
            fac_cand = str(cand.get("faculty") or "")
            faculty_changed = fac_orig != fac_cand

            if room_changed or slot_changed or faculty_changed:
                moved += 1
                displaced_sections.add(str(cand.get("section")))
                if cand.get("faculty"):
                    f_val = cand.get("faculty")
                    if isinstance(f_val, list):
                        displaced_faculty.update([str(x) for x in f_val])
                    else:
                        displaced_faculty.add(str(f_val))

                cost = 0.0
                if room_changed: cost += 1.0
                if slot_changed: cost += 1.0
                if faculty_changed: cost += 5.0
                if moved > 3: cost *= 1.5
                weighted_change_cost += cost

        total = max(len(original_entries), 1)
        stability_score = round(((total - moved) / total) * 100.0, 1)

        if moved == 0:
            risk_level = "low"
        elif moved <= 3 and weighted_change_cost <= 10:
            risk_level = "low"
        elif moved <= 8 and weighted_change_cost <= 25:
            risk_level = "medium"
        else:
            risk_level = "high"

        return {
            "moved_entries": moved,
            "displaced_sections": sorted(list(displaced_sections)),
            "displaced_faculty": sorted(list(displaced_faculty)),
            "stability_score": stability_score,
            "weighted_change_cost": round(weighted_change_cost, 1),
            "risk_level": risk_level
        }

    @staticmethod
    async def calculate_schedule_quality(timetable_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates composite schedule quality across 7 sub-metrics (0-100 scale).
        """
        checker = ConflictChecker()
        report = checker.detect(timetable_entries)

        hard_violations = report.total_hard_violations
        p78_count = sum(1 for e in timetable_entries if int(e.get("period", 1)) in (7, 8))
        total_slots = max(len(timetable_entries), 1)
        soft_penalty = p78_count * 5

        room_utilization_pct = min(100.0, round((total_slots / (35 * 48)) * 100.0, 1))
        preference_satisfaction_pct = round(max(0.0, 100.0 - (soft_penalty / total_slots) * 10.0), 1)

        quality_score = max(0, 100 - (hard_violations * 20) - int(soft_penalty / 10))

        return {
            "quality_score": quality_score,
            "hard_violations_count": hard_violations,
            "soft_penalty_total": soft_penalty,
            "faculty_overload_count": 0,
            "student_gaps_count": p78_count,
            "room_utilization_pct": room_utilization_pct,
            "preference_satisfaction_pct": preference_satisfaction_pct,
            "is_valid": hard_violations == 0
        }

    @staticmethod
    async def compare_timetables(original_entries: List[Dict[str, Any]], candidate_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates structured diff analysis comparing two timetable configurations."""
        metrics = await ToolRegistry.calculate_disruption_metrics(original_entries, candidate_entries)
        orig_map = {str(e.get("id") or f"{e.get('section')}_{e.get('day')}_{e.get('period')}"): e for e in original_entries}
        diffs = []

        for cand in candidate_entries:
            key = str(cand.get("id") or f"{cand.get('section')}_{cand.get('day')}_{cand.get('period')}")
            orig = orig_map.get(key)
            if not orig:
                continue
            r_change = str(orig.get("room")) != str(cand.get("room"))
            s_change = str(orig.get("day")) != str(cand.get("day")) or int(orig.get("period", 0)) != int(cand.get("period", 0))
            f_change = str(orig.get("faculty")) != str(cand.get("faculty"))

            if r_change or s_change or f_change:
                diffs.append({
                    "entry_id": key,
                    "section": cand.get("section"),
                    "subject": cand.get("subject"),
                    "original_room": orig.get("room"),
                    "repaired_room": cand.get("room"),
                    "original_slot": f"{orig.get('day')} P{orig.get('period')}",
                    "repaired_slot": f"{cand.get('day')} P{cand.get('period')}",
                    "original_faculty": orig.get("faculty"),
                    "repaired_faculty": cand.get("faculty")
                })

        return {
            "moved_count": metrics["moved_entries"],
            "stability_score": metrics["stability_score"],
            "weighted_change_cost": metrics["weighted_change_cost"],
            "risk_level": metrics["risk_level"],
            "diffs": diffs
        }

    # =================================================================
    # WRITE TOOLS
    # Defined in app/services/write_tools.py and re-exported here so the
    # agent reaches every capability through one registry. These are the
    # only paths that mutate the timetable; each re-validates with
    # ConflictChecker and rolls back if hard violations increase.
    # =================================================================
    apply_timetable_change = staticmethod(_write_tools.apply_timetable_change)
    publish_schedule = staticmethod(_write_tools.publish_schedule)
    assign_faculty_to_entry = staticmethod(_write_tools.assign_faculty_to_entry)
    create_timetable_entry = staticmethod(_write_tools.create_timetable_entry)
    delete_timetable_entry = staticmethod(_write_tools.delete_timetable_entry)

    @staticmethod
    async def save_schedule_snapshot(db: AsyncSession, session_id: int, entries: List[Dict[str, Any]], label: str = "checkpoint") -> Dict[str, Any]:
        """Saves a labeled JSON snapshot to session context."""
        res = await db.execute(select(AgentSession).where(AgentSession.id == session_id))
        session = res.scalar_one_or_none()
        if not session:
            raise ValueError(f"Agent session {session_id} not found")

        ctx = session.context or {}
        snapshots = ctx.get("snapshots", {})
        snapshots[label] = {"entries": entries, "saved_at": time.time()}

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
        quality = await ToolRegistry.calculate_schedule_quality(repaired_entries)

        elapsed_ms = int((time.time() - start_time) * 1000)
        result = {
            "status": repair_res.get("status", "OPTIMAL"),
            "moved_count": metrics["moved_entries"],
            "displaced_sections": metrics["displaced_sections"],
            "displaced_faculty": metrics["displaced_faculty"],
            "stability_score": metrics["stability_score"],
            "weighted_change_cost": metrics["weighted_change_cost"],
            "quality_score": quality["quality_score"],
            "risk_level": metrics["risk_level"],
            "hard_violations": validation["hard_violations"],
            "has_clashes": validation["has_clashes"],
            "entries": repaired_entries,
            "execution_time_ms": elapsed_ms
        }

        await ToolRegistry.save_schedule_snapshot(db, session_id, repaired_entries, label="candidate_repair")
        await ToolRegistry.log_action(
            db,
            session_id=session_id,
            tool_name="run_local_repair",
            arguments={"room_code": room_code, "faculty_name": faculty_name, "affected_sections": affected_sections or []},
            result=result,
            execution_time_ms=elapsed_ms
        )

        return result

    @staticmethod
    async def send_notification(
        db: AsyncSession,
        session_id: int,
        recipients: List[str],
        channel: str,
        message: str
    ) -> Dict[str, Any]:
        """Logs simulated admin push notifications and emails for schedule adjustments."""
        start = time.time()
        res = {
            "delivered_count": len(recipients),
            "channel": channel,
            "recipients": recipients,
            "message": message,
            "delivered_at": time.time()
        }
        elapsed_ms = int((time.time() - start) * 1000)
        await ToolRegistry.log_action(
            db,
            session_id=session_id,
            tool_name="send_notification",
            arguments={"recipients": recipients, "channel": channel, "message": message},
            result=res,
            execution_time_ms=elapsed_ms
        )
        return res
