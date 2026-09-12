import time
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import AgentSession, AgentEvent, AgentAction, AgentDecision
from app.models.faculty import Faculty
from app.models.timetable import TimetableEntry
from app.models.timetable_entry_faculty import TimetableEntryFaculty
from app.services.timetable_service import TimetableService
from app.services.tool_registry import ToolRegistry
from app.services import write_tools
try:
    from backend.solver.constraints import ConstraintRules
    from backend.solver.conflict_checker import ConflictChecker, faculty_identity_key
except (ImportError, ModuleNotFoundError):
    from solver.constraints import ConstraintRules
    from solver.conflict_checker import ConflictChecker, faculty_identity_key


class SubstituteDispatcher:
    """
    Autonomous Substitute Faculty Dispatcher.
    Detects faculty unavailability, analyzes impacted sections and slots,
    evaluates substitute candidates against AICTE workload and daily fatigue constraints,
    and executes safe, auditable substitute assignments.
    """

    @staticmethod
    async def find_impacted_slots(
        db: AsyncSession,
        faculty_name: str,
        version_id: int = 5,
        target_day: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Identifies all timetable entries currently assigned to the target faculty member."""
        tt_res = await TimetableService.get_version_timetable(db, version_id=version_id, section_name="ALL")
        all_entries = tt_res.get("entries", [])
        f_key = faculty_identity_key(faculty_name)

        impacted = []
        for e in all_entries:
            facs = e.get("faculty") or e.get("facultyNames") or []
            if isinstance(facs, str):
                fac_list = [f.strip() for f in facs.split(",") if f.strip()]
            else:
                fac_list = [str(f).strip() for f in facs if str(f).strip()]

            is_assigned = any(faculty_identity_key(f) == f_key for f in fac_list)
            if is_assigned:
                day = str(e.get("day", "")).upper()
                if not target_day or target_day.upper()[:3] == day[:3]:
                    impacted.append(dict(e))

        return impacted

    @staticmethod
    async def find_candidate_substitutes(
        db: AsyncSession,
        faculty_name: str,
        day: Optional[str] = None,
        period: Optional[int] = None,
        subject_code: Optional[str] = None,
        version_id: int = 5
    ) -> Dict[str, Any]:
        """
        Finds and ranks candidate substitute instructors for an impacted slot or general schedule.
        Enforces:
        - HC-02: Zero double-booking at (day, period)
        - SC-01 / HC-11: Weekly AICTE rank workload caps (Prof 12h, Assoc 14h, Asst 16h)
        - SC-02: Daily teaching cap (max 5 classes/day)
        """
        start_time = time.time()
        tt_res = await TimetableService.get_version_timetable(db, version_id=version_id, section_name="ALL")
        all_entries = tt_res.get("entries", [])
        f_key = faculty_identity_key(faculty_name)

        # 1. Compute current workload metrics across all faculty
        faculty_weekly_hours: Dict[str, int] = {}
        faculty_daily_hours: Dict[Tuple[str, str], int] = {}
        faculty_busy_slots: Set[Tuple[str, int, str]] = set()
        faculty_taught_subjects: Dict[str, Set[str]] = {}

        for e in all_entries:
            d = str(e.get("day", "")).upper()
            p = int(e.get("period", 1))
            subj = str(e.get("subject") or e.get("subjectCode") or "").strip().upper()
            facs = e.get("faculty") or e.get("facultyNames") or []
            if isinstance(facs, str):
                fac_list = [f.strip() for f in facs.split(",") if f.strip()]
            else:
                fac_list = [str(f).strip() for f in facs if str(f).strip()]

            for fac in fac_list:
                k = faculty_identity_key(fac)
                if not k:
                    continue
                faculty_weekly_hours[k] = faculty_weekly_hours.get(k, 0) + 1
                faculty_daily_hours[(k, d)] = faculty_daily_hours.get((k, d), 0) + 1
                faculty_busy_slots.add((k, d, p))
                if subj:
                    faculty_taught_subjects.setdefault(k, set()).add(subj)

        # 2. Get all faculty from database
        all_faculty = await ToolRegistry.get_faculty(db)
        candidates = []

        norm_day = str(day).upper() if day else None
        target_period = int(period) if period is not None else None
        norm_subj = str(subject_code).strip().upper() if subject_code else ""

        for member in all_faculty:
            cand_name = str(member.get("name") or "")
            cand_key = faculty_identity_key(cand_name)
            if not cand_key or cand_key == f_key:
                continue

            rank = str(member.get("designation") or "Assistant Professor")
            max_weekly = ConstraintRules.get_max_faculty_hours(rank)
            cur_weekly = faculty_weekly_hours.get(cand_key, 0)
            cur_daily = faculty_daily_hours.get((cand_key, norm_day), 0) if norm_day else 0

            # Constraint Checks
            is_busy_at_slot = False
            if norm_day and target_period:
                is_busy_at_slot = (cand_key, norm_day, target_period) in faculty_busy_slots

            has_weekly_capacity = (cur_weekly + 1) <= max_weekly
            has_daily_capacity = (cur_daily + 1) <= 5

            is_eligible = (not is_busy_at_slot) and has_weekly_capacity and has_daily_capacity

            # Suitability Scoring (0-100)
            score = 50.0
            if is_eligible:
                score += 20.0

            # Subject Match Boost
            taught = faculty_taught_subjects.get(cand_key, set())
            has_exact_subject = any(norm_subj in s for s in taught) if norm_subj else False
            if has_exact_subject:
                score += 25.0

            # Workload Fairness (prefer faculty with lighter load)
            load_ratio = cur_weekly / max(max_weekly, 1)
            score += max(0.0, (1.0 - load_ratio) * 15.0)

            # Deductions
            if is_busy_at_slot:
                score -= 60.0
            if not has_weekly_capacity:
                score -= 30.0
            if not has_daily_capacity:
                score -= 20.0

            suitability_label = "RECOMMENDED" if (is_eligible and has_exact_subject) else ("ELIGIBLE" if is_eligible else "INELIGIBLE")

            rejection_reasons = []
            if is_busy_at_slot:
                rejection_reasons.append(f"Busy on {norm_day} P{target_period}")
            if not has_weekly_capacity:
                rejection_reasons.append(f"Exceeds weekly cap ({cur_weekly}/{max_weekly}h)")
            if not has_daily_capacity:
                rejection_reasons.append(f"Exceeds daily cap ({cur_daily}h)")

            candidates.append({
                "id": member.get("id"),
                "name": cand_name,
                "designation": rank,
                "current_weekly_hours": cur_weekly,
                "max_weekly_hours": max_weekly,
                "daily_hours_at_target_day": cur_daily,
                "teaches_subject": has_exact_subject,
                "is_eligible": is_eligible,
                "suitability_score": round(max(0.0, min(100.0, score)), 1),
                "status": suitability_label,
                "rejection_reasons": rejection_reasons
            })

        # Sort: Eligible first, then highest score
        candidates.sort(key=lambda c: (c["is_eligible"], c["suitability_score"]), reverse=True)

        # Identify impacted timetable entry for absent faculty at target slot
        impacted_slot = None
        for e in all_entries:
            d = str(e.get("day", "")).upper()[:3]
            p = int(e.get("period", 1))
            facs = e.get("faculty") or e.get("facultyNames") or []
            if isinstance(facs, str):
                fac_list = [f.strip() for f in facs.split(",") if f.strip()]
            else:
                fac_list = [str(f).strip() for f in facs if str(f).strip()]
            if any(faculty_identity_key(f) == f_key for f in fac_list):
                if norm_day and d == norm_day[:3] and target_period and p == target_period:
                    impacted_slot = e
                    break
                elif not impacted_slot:
                    impacted_slot = e

        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "absent_faculty": faculty_name,
            "target_day": norm_day,
            "target_period": target_period,
            "subject": norm_subj,
            "impacted_slot": impacted_slot,
            "total_candidates": len(candidates),
            "eligible_candidates_count": sum(1 for c in candidates if c["is_eligible"]),
            "candidates": candidates,
            "execution_time_ms": elapsed_ms
        }

    @staticmethod
    async def dispatch_substitute(
        db: AsyncSession,
        session_id: int,
        entry_id: int,
        substitute_faculty_id: int,
        original_faculty_name: Optional[str] = None,
        reason: str = "Faculty medical / emergency leave"
    ) -> Dict[str, Any]:
        """
        Executes safe, auditable substitute dispatching for a specific timetable entry.
        Validates non-clash before committing and logs complete audit trace in Agent tables.
        """
        start_time = time.time()

        # 1. Fetch target entry
        stmt = select(TimetableEntry).where(TimetableEntry.id == entry_id)
        res = await db.execute(stmt)
        entry = res.scalar_one_or_none()
        if not entry:
            raise ValueError(f"Timetable entry ID {entry_id} not found")

        # 2. Fetch substitute faculty
        sub_res = await db.execute(select(Faculty).where(Faculty.id == substitute_faculty_id))
        substitute = sub_res.scalar_one_or_none()
        if not substitute:
            raise ValueError(f"Substitute faculty ID {substitute_faculty_id} not found")

        # 3. Pre-validation: ensure substitute has no double-booking at that time slot
        slot_id = entry.time_slot_id
        check_stmt = (
            select(TimetableEntry)
            .join(TimetableEntryFaculty, TimetableEntry.id == TimetableEntryFaculty.timetable_entry_id)
            .where(
                TimetableEntry.time_slot_id == slot_id,
                TimetableEntryFaculty.faculty_id == substitute_faculty_id,
                TimetableEntry.id != entry_id
            )
        )
        clash_res = await db.execute(check_stmt)
        if clash_res.scalars().first():
            raise ValueError(f"Cannot dispatch: Substitute {substitute.name} has a conflicting class in this time slot.")

        # 4. Save pre-dispatch snapshot
        tt_res = await TimetableService.get_version_timetable(db, version_id=entry.timetable_version_id, section_name="ALL")
        all_entries = tt_res.get("entries", [])
        await ToolRegistry.save_schedule_snapshot(db, session_id, all_entries, label=f"pre_substitute_dispatch_{entry_id}")

        # Determine the name of the original/replaced faculty
        old_text = original_faculty_name
        if not old_text:
            orig_facs = (
                await db.execute(
                    select(Faculty)
                    .join(TimetableEntryFaculty, Faculty.id == TimetableEntryFaculty.faculty_id)
                    .where(TimetableEntryFaculty.timetable_entry_id == entry_id)
                )
            ).scalars().all()
            if orig_facs:
                old_text = ", ".join(f.name for f in orig_facs)
            else:
                old_text = "assigned faculty"

        # 5. Execute reassignment
        # Target and delete only the specific absent faculty to preserve lab co-instructors
        target_deleted = False
        orig_fac = None
        if original_faculty_name:
            all_fac_res = await db.execute(select(Faculty))
            all_facs = all_fac_res.scalars().all()
            target_key = faculty_identity_key(original_faculty_name)
            for f in all_facs:
                if f.name == original_faculty_name or (target_key and faculty_identity_key(f.name) == target_key):
                    orig_fac = f
                    break
            if orig_fac:
                matching_assocs = (
                    await db.execute(
                        select(TimetableEntryFaculty).where(
                            TimetableEntryFaculty.timetable_entry_id == entry_id,
                            TimetableEntryFaculty.faculty_id == orig_fac.id
                        )
                    )
                ).scalars().all()
                for ef in matching_assocs:
                    await db.delete(ef)
                if matching_assocs:
                    await db.flush()
                    target_deleted = True

        existing_assocs = []
        if not target_deleted:
            existing_assocs = (
                await db.execute(
                    select(TimetableEntryFaculty).where(TimetableEntryFaculty.timetable_entry_id == entry_id)
                )
            ).scalars().all()
            if len(existing_assocs) <= 1:
                for ef in existing_assocs:
                    await db.delete(ef)
                if existing_assocs:
                    await db.flush()

        new_assoc = TimetableEntryFaculty(timetable_entry_id=entry_id, faculty_id=substitute_faculty_id)
        db.add(new_assoc)

        # Update JSON faculty_ids array to stay in sync with TimetableEntryFaculty
        current_fids = list(entry.faculty_ids) if isinstance(entry.faculty_ids, list) else []
        if orig_fac and orig_fac.id in current_fids:
            current_fids = [fid for fid in current_fids if fid != orig_fac.id]
        elif not target_deleted and len(existing_assocs) <= 1:
            current_fids = []
        if substitute_faculty_id not in current_fids:
            current_fids.append(substitute_faculty_id)
        entry.faculty_ids = current_fids
        await db.flush()

        # 6. Post-verification: ConflictChecker audit
        verify_res = await TimetableService.get_version_timetable(db, version_id=entry.timetable_version_id, section_name="ALL")
        checker = ConflictChecker()
        report = checker.detect(verify_res.get("entries", []))

        if report.faculty_clashes > 0:
            await db.rollback()
            raise ValueError(f"Dispatch aborted: resulted in {report.faculty_clashes} faculty collision(s).")

        # 7. Persist Agent Event & Decision
        # Ensure session exists to avoid FK constraint failure
        sess_check = (await db.execute(select(AgentSession.id).where(AgentSession.id == session_id))).scalar_one_or_none()
        if not sess_check:
            fallback_sess = AgentSession(goal="Substitute Faculty Dispatch", status="active")
            db.add(fallback_sess)
            await db.flush()
            session_id = fallback_sess.id

        summary = f"Substitute Dispatch: Assigned {substitute.name} in place of {old_text} for Entry #{entry_id} ({reason})."
        event = AgentEvent(
            session_id=session_id,
            event_type="SUBSTITUTE_DISPATCHED",
            source="substitute_dispatcher",
            severity="low",
            summary=summary,
            payload={
                "entry_id": entry_id,
                "original_faculty": old_text,
                "substitute_faculty_id": substitute.id,
                "substitute_faculty_name": substitute.name,
                "reason": reason
            }
        )
        db.add(event)

        decision = AgentDecision(
            session_id=session_id,
            decision_type="SUBSTITUTE_DISPATCH",
            reason_code="FACULTY_UNAVAILABLE",
            selected_option=f"assign_{substitute.name}",
            risk_level="low",
            rationale=summary,
            payload={"entry_id": entry_id, "substitute_name": substitute.name}
        )
        db.add(decision)
        await db.commit()

        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "status": "DISPATCHED",
            "entry_id": entry_id,
            "original_faculty": old_text,
            "substitute_faculty_id": substitute.id,
            "substitute_faculty_name": substitute.name,
            "summary": summary,
            "total_hard_violations_after": report.total_hard_violations,
            "execution_time_ms": elapsed_ms
        }
