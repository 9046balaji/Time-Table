import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import AgentSession, AgentEvent, AgentDecision
from app.services.tool_registry import ToolRegistry
from backend.solver.conflict_checker import ConflictChecker


class MultiAgentConsensusEngine:
    """
    Multi-Agent Consensus Verification Protocol Engine.
    Executes role-based verification across 3 specialized sub-agent roles:
    - ARCHITECT: Dynamically queries database room metadata to validate room capacities and lab type compatibility.
    - SOLVER: Validates slot compacting and soft constraint penalty optimization.
    - VALIDATOR: Performs ground-truth hard constraint conflict analysis (0 clashes required, holds VETO power).
    """

    @staticmethod
    async def evaluate_consensus(
        db: AsyncSession,
        session_id: int,
        timetable_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Runs role-based multi-agent consensus voting on a target candidate timetable."""
        start_time = time.time()
        res = await db.execute(select(AgentSession).where(AgentSession.id == session_id))
        session = res.scalar_one_or_none()
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        # The candidate schedule is the agent's own working memory, not something
        # the caller supplies. Trusting the request body meant POSTing an empty body
        # produced a unanimous 3/3 APPROVE over zero entries, which silently bypassed
        # the VALIDATOR veto that is supposed to gate every publish.
        context = session.context or {}
        if not timetable_entries:
            timetable_entries = context.get("candidate_entries") or []

        if not timetable_entries:
            # Nothing to verify. An agent must never report "approved" when it
            # validated nothing, so this is a veto, not a pass.
            return {
                "session_id": session_id,
                "consensus_passed": False,
                "status": "VETOED",
                "votes": [{
                    "role": "VALIDATOR",
                    "vote": "REJECT",
                    "has_veto_power": True,
                    "hard_violations": 0,
                    "rationale": "VETO: no candidate schedule to verify. Run a repair "
                                 "before requesting consensus.",
                }],
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "summary": "Multi-Agent Consensus VETOED: no candidate schedule available to verify.",
            }

        # 1. VALIDATOR Sub-Agent (Ground-Truth Hard Conflict Analysis & VETO Power)
        checker = ConflictChecker()
        report = checker.detect(timetable_entries)
        validator_passed = (report.total_hard_violations == 0)
        validator_vote = {
            "role": "VALIDATOR",
            "vote": "APPROVE" if validator_passed else "REJECT",
            "has_veto_power": True,
            "hard_violations": report.total_hard_violations,
            "room_clashes": report.physical_room_clashes,
            "joint_section_slots": report.joint_section_slots,
            "faculty_clashes": report.faculty_clashes,
            "student_clashes": report.student_clashes,
            "rationale": "Zero hard constraint violations detected. Ground truth verified." if validator_passed else f"VETO: {report.total_hard_violations} hard violation(s) detected ({report.physical_room_clashes} room, {report.faculty_clashes} faculty, {report.student_clashes} student). {report.joint_section_slots} joint-section share(s) ignored as legitimate."
        }

        # 2. ARCHITECT Sub-Agent (Dynamic Database Room Queries & Type Compatibility)
        rooms = await ToolRegistry.get_rooms(db)
        room_map = {str(r.get("code") or r.get("id")).upper(): r for r in rooms}
        capacity_issues = 0
        lab_type_mismatches = 0

        for e in timetable_entries:
            room_code = str(e.get("room", "")).strip().upper()
            subj_text = str(e.get("subject", "")).strip()
            e_type = str(e.get("entry_type") or "").upper()
            is_lab_subject = (
                "(P)" in subj_text or "(P)" in subj_text.upper() or
                "LAB" in subj_text.upper() or "PRACTICAL" in subj_text.upper() or
                e_type in ("P", "T&P")
            )

            if room_code and room_code in room_map:
                r_info = room_map[room_code]
                cap = int(r_info.get("capacity", 60))
                r_type = str(r_info.get("room_type", "classroom")).lower()

                if cap < 30:
                    capacity_issues += 1
                if is_lab_subject and "lab" not in r_type and room_code not in ['604', '605', '606', '611', '612', '615', '616', '617', 'AFTF-12', 'AFTF-13', 'AFTF-14']:
                    lab_type_mismatches += 1

        architect_passed = (capacity_issues <= 2 and lab_type_mismatches == 0)
        architect_vote = {
            "role": "ARCHITECT",
            "vote": "APPROVE" if architect_passed else "REJECT",
            "has_veto_power": False,
            "capacity_issues": capacity_issues,
            "lab_type_mismatches": lab_type_mismatches,
            "rationale": "Dynamic room capacities and lab venue assignments are architecturally valid." if architect_passed else f"Architectural mismatch: {lab_type_mismatches} lab venue mismatch(es), {capacity_issues} capacity alert(s)."
        }

        # 3. SOLVER Sub-Agent (Soft Constraint SC-07 Afternoon Slot Compactness)
        p78_slots = sum(1 for e in timetable_entries if int(e.get("period", 1)) in (7, 8))
        total_slots = max(len(timetable_entries), 1)
        late_ratio = round((p78_slots / total_slots) * 100.0, 1)

        # VFSTR Policy SC-07: Afternoon slot (P7-P8) ratio should remain under 40% per section
        solver_passed = (late_ratio <= 40.0)
        solver_vote = {
            "role": "SOLVER",
            "vote": "APPROVE" if solver_passed else "REJECT",
            "has_veto_power": False,
            "late_slot_pct": late_ratio,
            "policy_rule": "SC-07",
            "rationale": f"SC-07 Soft Constraint satisfied ({late_ratio}% late P7-P8 slots <= 40% policy threshold)." if solver_passed else f"SC-07 Soft Constraint threshold exceeded ({late_ratio}% late P7-P8 slots > 40% cap)."
        }

        # Overall Consensus Protocol (VALIDATOR Veto + Unanimous/Majority Rule)
        consensus_passed = validator_passed and architect_passed and solver_passed
        elapsed_ms = int((time.time() - start_time) * 1000)

        if not validator_passed:
            summary = f"Multi-Agent Consensus REJECTED (VALIDATOR Veto): {validator_vote['rationale']}"
        elif consensus_passed:
            summary = "Multi-Agent Consensus APPROVED: Unanimous 3/3 roles (VALIDATOR, ARCHITECT, SOLVER) voted APPROVE."
        else:
            rejected_roles = [v["role"] for v in [architect_vote, solver_vote] if v["vote"] == "REJECT"]
            summary = f"Multi-Agent Consensus HELD: Rejected by {', '.join(rejected_roles)}. Human review required."

        result_payload = {
            "session_id": session_id,
            "consensus_passed": consensus_passed,
            "status": "APPROVED" if consensus_passed else "HELD",
            # Always state what was actually verified, so an approval can never
            # look authoritative without disclosing its evidence base.
            "entries_verified": len(timetable_entries),
            "votes": [validator_vote, architect_vote, solver_vote],
            "execution_time_ms": elapsed_ms,
            "summary": summary
        }

        # Persist Agent Decision Trace
        decision = AgentDecision(
            session_id=session.id,
            decision_type="MULTI_AGENT_CONSENSUS",
            reason_code="PRE_PUBLICATION_VERIFICATION",
            selected_option="APPROVE_PUBLICATION" if consensus_passed else "HOLD_PUBLICATION",
            risk_level="low" if consensus_passed else "high",
            rationale=summary,
            payload=result_payload
        )
        db.add(decision)

        event = AgentEvent(
            session_id=session.id,
            event_type="CONSENSUS_EVALUATED",
            source="multi_agent_consensus",
            severity="low" if consensus_passed else "high",
            summary=summary,
            payload=result_payload
        )
        db.add(event)
        await db.commit()

        return result_payload
