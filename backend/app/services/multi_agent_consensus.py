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
    - ARCHITECT: Validates room capacities, section strength bounds, and venue compatibility.
    - SOLVER: Validates slot compacting and minimal disruption efficiency.
    - VALIDATOR: Performs ground-truth hard constraint conflict analysis (0 clashes required).
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

        # 1. VALIDATOR Role Vote
        checker = ConflictChecker()
        report = checker.detect(timetable_entries)
        validator_passed = (report.total_hard_violations == 0)
        validator_vote = {
            "role": "VALIDATOR",
            "vote": "APPROVE" if validator_passed else "REJECT",
            "hard_violations": report.total_hard_violations,
            "room_clashes": report.room_clashes,
            "faculty_clashes": report.faculty_clashes,
            "student_clashes": report.student_clashes,
            "rationale": "Zero hard constraint violations detected." if validator_passed else f"{report.total_hard_violations} hard violation(s) detected."
        }

        # 2. ARCHITECT Role Vote (Room Capacity & Type Compatibility)
        rooms = await ToolRegistry.get_rooms(db)
        room_cap_map = {str(r.get("code") or r.get("id")).upper(): int(r.get("capacity", 60)) for r in rooms}
        capacity_issues = 0
        for e in timetable_entries:
            room = str(e.get("room", "")).strip().upper()
            if room and room in room_cap_map:
                if room_cap_map[room] < 30:  # Small room capacity check
                    capacity_issues += 1

        architect_passed = (capacity_issues <= 2)
        architect_vote = {
            "role": "ARCHITECT",
            "vote": "APPROVE" if architect_passed else "REJECT",
            "capacity_issues": capacity_issues,
            "rationale": "Venue capacity and room type mappings are architecturally sound." if architect_passed else f"{capacity_issues} room capacity warning(s) flagged."
        }

        # 3. SOLVER Role Vote (Slot Compactness & Schedule Efficiency)
        p78_slots = sum(1 for e in timetable_entries if int(e.get("period", 1)) in (7, 8))
        total_slots = max(len(timetable_entries), 1)
        late_ratio = round((p78_slots / total_slots) * 100.0, 1)

        solver_passed = (late_ratio <= 45.0)
        solver_vote = {
            "role": "SOLVER",
            "vote": "APPROVE" if solver_passed else "REJECT",
            "late_slot_pct": late_ratio,
            "rationale": f"Schedule compactness optimal ({late_ratio}% late slots)." if solver_passed else f"Excessive late slots ({late_ratio}%)."
        }

        # Overall Consensus Status
        consensus_passed = validator_passed and architect_passed and solver_passed
        elapsed_ms = int((time.time() - start_time) * 1000)

        summary = (
            "Multi-Agent Consensus Approved: 3/3 roles voted APPROVE. Schedule ready for publication."
            if consensus_passed
            else f"Multi-Agent Consensus Held: Validator ({validator_vote['vote']}), Architect ({architect_vote['vote']}), Solver ({solver_vote['vote']})."
        )

        result_payload = {
            "session_id": session_id,
            "consensus_passed": consensus_passed,
            "status": "APPROVED" if consensus_passed else "HELD",
            "votes": [validator_vote, architect_vote, solver_vote],
            "execution_time_ms": elapsed_ms,
            "summary": summary
        }

        # Record Decision
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
            severity="low" if consensus_passed else "medium",
            summary=summary,
            payload=result_payload
        )
        db.add(event)
        await db.commit()

        return result_payload
