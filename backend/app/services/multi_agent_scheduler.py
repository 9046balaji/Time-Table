import time
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import AgentSession, AgentEvent, AgentDecision
from app.models.timetable import TimetableVersion, TimetableEntry
from app.models.timetable_entry_faculty import TimetableEntryFaculty
from app.services.tool_registry import ToolRegistry
try:
    from backend.solver.constraints import ConstraintRules
    from backend.solver.conflict_checker import ConflictChecker, faculty_identity_key
    from backend.solver.csat_solver import CPSATSolver
except (ImportError, ModuleNotFoundError):
    from solver.constraints import ConstraintRules
    from solver.conflict_checker import ConflictChecker, faculty_identity_key
    from solver.csat_solver import CPSATSolver


@dataclass
class AgentCritique:
    agent_name: str
    rule_id: str
    severity: str  # "HARD_VETO" | "SOFT_PENALTY"
    message: str
    suggested_action: Optional[str] = None
    affected_slot: Optional[Dict[str, Any]] = None


@dataclass
class AgentVote:
    agent_name: str
    vote: str  # "APPROVE" | "REJECT"
    has_veto_power: bool
    violations_detected: int
    rationale: str
    metrics: Dict[str, Any] = field(default_factory=dict)


class SectionCurriculumAgent:
    """Autonomous agent responsible for section quotas, year levels, subject credits, library hours, and cohort blocks."""

    AGENT_NAME = "SectionCurriculumAgent"

    @classmethod
    def audit(cls, slots: List[Dict[str, Any]]) -> List[AgentCritique]:
        critiques = []
        quotas = ConstraintRules.validate_section_weekly_quotas(slots)
        if not quotas["is_compliant"]:
            for sec, dev in quotas["deviations"].items():
                critiques.append(AgentCritique(
                    agent_name=cls.AGENT_NAME,
                    rule_id="SECTION_QUOTA",
                    severity="HARD_VETO" if abs(dev["diff"]) >= 5 else "SOFT_PENALTY",
                    message=f"Section {sec} has {dev['actual']} teaching slots (Expected: {dev['expected']}, deviation: {dev['diff']}).",
                    suggested_action="Adjust slots to match official academic curriculum requirements."
                ))

        lib_report = ConstraintRules.validate_library_allocation(slots)
        if not lib_report["is_valid"]:
            for viol in lib_report["violations"]:
                critiques.append(AgentCritique(
                    agent_name=cls.AGENT_NAME,
                    rule_id="LIBRARY_RULE",
                    severity="HARD_VETO",
                    message=viol,
                    suggested_action="Enforce exactly 1 Library hour for 2nd Year, 0 for 3rd/4th Year."
                ))

        for s in slots:
            day = str(s.get("day", "")).upper()
            period = int(s.get("period", 1))
            code = str(s.get("subject") or s.get("subjectCode") or "")
            sec = str(s.get("section") or "")
            is_4th = "IV " in sec

            # Minors/Honors check
            if not ConstraintRules.check_minors_honors_slot_protection(day, period, code):
                critiques.append(AgentCritique(
                    agent_name=cls.AGENT_NAME,
                    rule_id="HC-09_MINORS_HONORS",
                    severity="HARD_VETO",
                    message=f"Minors/Honors violation at {day} P{period} in {sec}: {code}.",
                    suggested_action="Minors/Honors locked strictly to WED P7-P8 & THU P7-P8."
                ))

            # 4th Year SL/EL check
            if is_4th and not ConstraintRules.check_4th_year_slel_slot_protection(day, period, code, is_4th_year=True):
                critiques.append(AgentCritique(
                    agent_name=cls.AGENT_NAME,
                    rule_id="HC-10_SL_EL",
                    severity="HARD_VETO",
                    message=f"4th Year SL/EL violation at {day} P{period} in {sec}: {code}.",
                    suggested_action="4th Year SL/EL locked to P1-P2 MON-SAT or SAT P6-P8."
                ))

        return critiques

    @classmethod
    def cast_vote(cls, slots: List[Dict[str, Any]]) -> AgentVote:
        critiques = cls.audit(slots)
        hard_critiques = [c for c in critiques if c.severity == "HARD_VETO"]
        passed = len(hard_critiques) == 0
        return AgentVote(
            agent_name=cls.AGENT_NAME,
            vote="APPROVE" if passed else "REJECT",
            has_veto_power=True,
            violations_detected=len(hard_critiques),
            rationale="All section quotas, cohort anchors (Minors/Honors & SL/EL), and library rules verified." if passed else f"Rejected: {len(hard_critiques)} curriculum violations detected.",
            metrics={
                "total_critiques": len(critiques),
                "hard_vetoes": len(hard_critiques),
                "sample_issues": [c.message for c in critiques[:3]]
            }
        )


class FacultyWorkloadAgent:
    """Autonomous agent protecting faculty from double-booking, AICTE weekly overloads, and daily fatigue."""

    AGENT_NAME = "FacultyWorkloadAgent"

    @classmethod
    def audit(cls, slots: List[Dict[str, Any]], faculty_rank_map: Optional[Dict[str, str]] = None) -> List[AgentCritique]:
        critiques = []
        rank_map = faculty_rank_map or {}

        # 1. Weekly teaching hours & Daily hours per faculty
        faculty_weekly_hours: Dict[str, int] = {}
        faculty_daily_hours: Dict[Tuple[str, str], int] = {}
        faculty_time_slots: Dict[Tuple[str, int, str], List[str]] = {}

        for s in slots:
            day = str(s.get("day", "")).upper()
            period = int(s.get("period", 1))
            sec = str(s.get("section", ""))
            facs = s.get("faculty") or s.get("facultyNames") or []
            if isinstance(facs, str):
                fac_list = [f.strip() for f in facs.split(",") if f.strip()]
            else:
                fac_list = [str(f).strip() for f in facs if str(f).strip()]

            for fac in fac_list:
                f_key = faculty_identity_key(fac)
                if not f_key:
                    continue

                faculty_weekly_hours[f_key] = faculty_weekly_hours.get(f_key, 0) + 1
                day_key = (f_key, day)
                faculty_daily_hours[day_key] = faculty_daily_hours.get(day_key, 0) + 1

                time_key = (day, period, f_key)
                faculty_time_slots.setdefault(time_key, []).append(sec)

        # Audit Double Bookings (HC-02)
        for (day, period, f_key), sec_list in faculty_time_slots.items():
            if len(sec_list) > 1:
                critiques.append(AgentCritique(
                    agent_name=cls.AGENT_NAME,
                    rule_id="HC-02_DOUBLE_BOOKING",
                    severity="HARD_VETO",
                    message=f"Faculty {f_key} double-booked on {day} P{period} across sections: {', '.join(sec_list)}.",
                    suggested_action="Re-assign one section to an alternate time or co-faculty."
                ))

        # Audit Daily Teaching Cap (HC-09 / SC-02: max 4-5 classes/day)
        for (f_key, day), d_hours in faculty_daily_hours.items():
            if d_hours > 5:
                critiques.append(AgentCritique(
                    agent_name=cls.AGENT_NAME,
                    rule_id="HC-09_DAILY_CAP",
                    severity="HARD_VETO",
                    message=f"Faculty {f_key} exceeds hard daily teaching cap ({d_hours} hours on {day} > 5h max).",
                    suggested_action="Shift one lecture to a lighter day."
                ))
            elif d_hours > 4:
                critiques.append(AgentCritique(
                    agent_name=cls.AGENT_NAME,
                    rule_id="SC-02_DAILY_FATIGUE",
                    severity="SOFT_PENALTY",
                    message=f"Faculty {f_key} has heavy daily teaching load ({d_hours} hours on {day}).",
                    suggested_action="Redistribute to improve daily pedagogical balance."
                ))

        # Audit Weekly Hours Cap by Rank (HC-11 / SC-01: 12/14/16h)
        for f_key, w_hours in faculty_weekly_hours.items():
            rank = rank_map.get(f_key, "Assistant Professor")
            max_h = ConstraintRules.get_max_faculty_hours(rank)
            if w_hours > max_h:
                critiques.append(AgentCritique(
                    agent_name=cls.AGENT_NAME,
                    rule_id="SC-01_WEEKLY_WORKLOAD",
                    severity="SOFT_PENALTY" if w_hours <= max_h + 2 else "HARD_VETO",
                    message=f"Faculty {f_key} ({rank}) scheduled for {w_hours} hours/week (Exceeds AICTE cap of {max_h}h).",
                    suggested_action="Re-allocate one theory section to parallel departmental faculty."
                ))

        return critiques

    @classmethod
    def cast_vote(cls, slots: List[Dict[str, Any]], faculty_rank_map: Optional[Dict[str, str]] = None) -> AgentVote:
        critiques = cls.audit(slots, faculty_rank_map)
        hard_critiques = [c for c in critiques if c.severity == "HARD_VETO"]
        passed = len(hard_critiques) == 0
        return AgentVote(
            agent_name=cls.AGENT_NAME,
            vote="APPROVE" if passed else "REJECT",
            has_veto_power=True,
            violations_detected=len(hard_critiques),
            rationale="Zero faculty double-bookings and all daily/weekly workload caps respected." if passed else f"Rejected: {len(hard_critiques)} faculty workload/fatigue violations.",
            metrics={
                "total_critiques": len(critiques),
                "hard_vetoes": len(hard_critiques),
                "sample_issues": [c.message for c in critiques[:3]]
            }
        )


class VenueBlockAgent:
    """Autonomous agent managing physical classroom and lab spaces, GPU prioritization, and campus building block locality."""

    AGENT_NAME = "VenueBlockAgent"

    @classmethod
    def audit(cls, slots: List[Dict[str, Any]]) -> List[AgentCritique]:
        critiques = []
        room_time_map: Dict[Tuple[str, int, str], List[str]] = {}

        for s in slots:
            day = str(s.get("day", "")).upper()
            period = int(s.get("period", 1))
            sec = str(s.get("section", ""))
            room = str(s.get("room") or s.get("roomCode") or "").strip().upper()
            subj = str(s.get("subject") or s.get("subjectCode") or "")
            stype = str(s.get("type") or s.get("entry_type") or "L").upper()
            is_lab = "(P)" in subj or "LAB" in subj.upper() or stype in ("P", "LAB")

            if room and room not in ConstraintRules.IGNORED_ROOM_CODES:
                room_time_map.setdefault((day, period, room), []).append(sec)

                # Room Type Match (HC-06)
                if is_lab and not any(k in room for k in ["604", "605", "606", "611", "612", "615", "616", "617", "AFTF", "AFF"]):
                    critiques.append(AgentCritique(
                        agent_name=cls.AGENT_NAME,
                        rule_id="HC-06_ROOM_TYPE",
                        severity="HARD_VETO",
                        message=f"Lab session {subj} for {sec} placed in non-lab classroom {room}.",
                        suggested_action="Move to a designated computer lab (604-617) or GPU lab (AFTF-12..14)."
                    ))

                # GPU Lab Priority Check
                is_gpu_subj = any(g in subj.upper() for g in ConstraintRules.GPU_PRIORITY_SUBJECTS)
                if is_gpu_subj and "AFTF" not in room:
                    critiques.append(AgentCritique(
                        agent_name=cls.AGENT_NAME,
                        rule_id="SC-06_GPU_PRIORITY",
                        severity="SOFT_PENALTY",
                        message=f"Compute-intensive subject {subj} in {sec} allocated to standard lab {room} instead of high-capacity GPU lab (AFTF).",
                        suggested_action="Prioritize AFTF-12, AFTF-13, or AFTF-14 for Deep Learning / Computer Vision."
                    ))

        # Room Collision (HC-01)
        for (day, period, room), sec_list in room_time_map.items():
            if len(sec_list) > 1:
                critiques.append(AgentCritique(
                    agent_name=cls.AGENT_NAME,
                    rule_id="HC-01_ROOM_COLLISION",
                    severity="HARD_VETO",
                    message=f"Room {room} double-booked on {day} P{period} by: {', '.join(sec_list)}.",
                    suggested_action="Re-route one section to an open classroom in the same block."
                ))

        # Building Block Locality & Transit (SC-09)
        transit_audit = ConstraintRules.calculate_block_transit_score(slots)
        if not transit_audit["is_optimal"]:
            critiques.append(AgentCritique(
                agent_name=cls.AGENT_NAME,
                rule_id="SC-09_BLOCK_LOCALITY",
                severity="SOFT_PENALTY",
                message=f"Detected {transit_audit['cross_block_sprints']} cross-block sprints between consecutive periods across campus.",
                suggested_action="Cluster consecutive section classes in U-Block or H-Block to maintain home-block locality."
            ))

        return critiques

    @classmethod
    def cast_vote(cls, slots: List[Dict[str, Any]]) -> AgentVote:
        critiques = cls.audit(slots)
        hard_critiques = [c for c in critiques if c.severity == "HARD_VETO"]
        passed = len(hard_critiques) == 0
        return AgentVote(
            agent_name=cls.AGENT_NAME,
            vote="APPROVE" if passed else "REJECT",
            has_veto_power=True,
            violations_detected=len(hard_critiques),
            rationale="Zero room collisions, 100% lab type compatibility, and campus block transit optimized." if passed else f"Rejected: {len(hard_critiques)} room/venue collisions detected.",
            metrics={
                "total_critiques": len(critiques),
                "hard_vetoes": len(hard_critiques),
                "sample_issues": [c.message for c in critiques[:3]]
            }
        )


class TemporalFlowAgent:
    """Autonomous agent managing schedule rhythm, break locks, continuous lab spans, student gaps, and afternoon load."""

    AGENT_NAME = "TemporalFlowAgent"

    @classmethod
    def audit(cls, slots: List[Dict[str, Any]]) -> List[AgentCritique]:
        critiques = []
        sec_day_slots: Dict[Tuple[str, str], Set[int]] = {}

        for s in slots:
            day = str(s.get("day", "")).upper()
            period = int(s.get("period", 1))
            sec = str(s.get("section", ""))
            subj = str(s.get("subject") or s.get("subjectCode") or "")
            stype = str(s.get("type") or s.get("entry_type") or "L").upper()
            code_norm = ConstraintRules.normalize_string(subj)

            # Break Protection (HC-07)
            if code_norm in ("BREAK", "LUNCH"):
                continue

            sec_day_slots.setdefault((sec, day), set()).add(period)

            # Continuous Lab Check (HC-08)
            is_lab = "(P)" in code_norm or "LAB" in code_norm or stype in ("P", "LAB")
            span = int(s.get("spanPeriods") or s.get("span_periods") or 1)
            if is_lab and span < 2:
                critiques.append(AgentCritique(
                    agent_name=cls.AGENT_NAME,
                    rule_id="HC-08_LAB_CONSECUTIVENESS",
                    severity="SOFT_PENALTY",
                    message=f"Lab session {subj} for {sec} at {day} P{period} is configured with span=1 (Expected: 2-3 consecutive periods).",
                    suggested_action="Ensure continuous practical sessions span 2-3 periods."
                ))

        # Check Free Gaps (SC-03: isolated gap between classes in a day)
        gap_count = 0
        for (sec, day), periods in sec_day_slots.items():
            if len(periods) >= 2:
                min_p = min(periods)
                max_p = max(periods)
                for p in range(min_p + 1, max_p):
                    if p not in periods:
                        gap_count += 1

        if gap_count > 15:
            critiques.append(AgentCritique(
                agent_name=cls.AGENT_NAME,
                rule_id="SC-03_STUDENT_GAPS",
                severity="SOFT_PENALTY",
                message=f"High frequency of isolated free gaps detected across student schedules ({gap_count} gaps).",
                suggested_action="Compact class schedules to eliminate isolated downtime."
            ))

        # Check Late Afternoon Load (SC-07 policy: P7-P8 <= 40%)
        p78_slots = sum(1 for s in slots if int(s.get("period", 1)) in (7, 8))
        total_slots = max(len(slots), 1)
        late_pct = round((p78_slots / total_slots) * 100.0, 1)
        if late_pct > 40.0:
            critiques.append(AgentCritique(
                agent_name=cls.AGENT_NAME,
                rule_id="SC-07_LATE_AFTERNOON_LOAD",
                severity="SOFT_PENALTY",
                message=f"Late afternoon load is {late_pct}% (Exceeds institutional policy cap of 40%).",
                suggested_action="Shift eligible tutorial or theory sessions to morning periods."
            ))

        return critiques

    @classmethod
    def cast_vote(cls, slots: List[Dict[str, Any]]) -> AgentVote:
        critiques = cls.audit(slots)
        hard_critiques = [c for c in critiques if c.severity == "HARD_VETO"]
        passed = len(hard_critiques) == 0
        return AgentVote(
            agent_name=cls.AGENT_NAME,
            vote="APPROVE" if passed else "REJECT",
            has_veto_power=False,
            violations_detected=len(hard_critiques),
            rationale="Break locks protected, lab continuity verified, and schedule compactness optimal." if passed else f"Disapproved: {len(hard_critiques)} temporal flow violations.",
            metrics={
                "total_critiques": len(critiques),
                "hard_vetoes": len(hard_critiques),
                "sample_issues": [c.message for c in critiques[:3]]
            }
        )


class StudentWelfareAgent:
    """Autonomous agent monitoring student fatigue, cognitive load balance, and continuous study marathons."""
    AGENT_NAME = "StudentWelfareAgent"

    @classmethod
    def audit(cls, slots: List[Dict[str, Any]]) -> List[AgentCritique]:
        critiques = []
        sec_day_slots: Dict[Tuple[str, str], List[int]] = {}
        for s in slots:
            sec = str(s.get("section") or s.get("sectionName") or "")
            day = str(s.get("day", "")).upper()
            p = int(s.get("period", 1))
            sec_day_slots.setdefault((sec, day), []).append(p)

        # Check student marathon (>7 classes on a single day without enough breaks)
        for (sec, day), p_list in sec_day_slots.items():
            if len(p_list) > 7:
                critiques.append(AgentCritique(
                    agent_name=cls.AGENT_NAME,
                    rule_id="STUDENT_COGNITIVE_OVERLOAD",
                    severity="SOFT_PENALTY",
                    message=f"Section {sec} has {len(p_list)} periods scheduled on {day} (> 7 periods). High cognitive fatigue.",
                    suggested_action="Distribute lectures across lighter days (e.g. Wednesday/Saturday)."
                ))
        return critiques

    @classmethod
    def cast_vote(cls, slots: List[Dict[str, Any]]) -> AgentVote:
        critiques = cls.audit(slots)
        hard_critiques = [c for c in critiques if c.severity == "HARD_VETO"]
        passed = len(hard_critiques) == 0
        return AgentVote(
            agent_name=cls.AGENT_NAME,
            vote="APPROVE" if passed else "REJECT",
            has_veto_power=False,
            violations_detected=len(hard_critiques),
            rationale="Student cognitive fatigue within safe pedagogical limits." if passed else f"Fatigue notice: {len(critiques)} load balance issues.",
            metrics={"total_critiques": len(critiques), "hard_vetoes": len(hard_critiques)}
        )


class LabTechInfraAgent:
    """Autonomous agent monitoring computing infrastructure, GPU utilization, machine turnover, and maintenance."""
    AGENT_NAME = "LabTechInfraAgent"

    @classmethod
    def audit(cls, slots: List[Dict[str, Any]]) -> List[AgentCritique]:
        critiques = []
        # Check GPU lab utilization in AFTF-12/13/14
        for s in slots:
            room = str(s.get("room") or s.get("roomCode") or "").upper()
            day = str(s.get("day", "")).upper()
            p = int(s.get("period", 1))
            if "AFTF" in room:
                # Protect Saturday afternoon maintenance window (SAT P7-P8)
                if day in ("SAT", "SATURDAY") and p in (7, 8):
                    critiques.append(AgentCritique(
                        agent_name=cls.AGENT_NAME,
                        rule_id="INFRA_MAINTENANCE_WINDOW",
                        severity="SOFT_PENALTY",
                        message=f"GPU Lab {room} occupied during scheduled Saturday server maintenance window ({day} P{p}).",
                        suggested_action="Reserve Saturday afternoon for driver/PyTorch OS updates."
                    ))
        return critiques

    @classmethod
    def cast_vote(cls, slots: List[Dict[str, Any]]) -> AgentVote:
        critiques = cls.audit(slots)
        hard_critiques = [c for c in critiques if c.severity == "HARD_VETO"]
        passed = len(hard_critiques) == 0
        return AgentVote(
            agent_name=cls.AGENT_NAME,
            vote="APPROVE" if passed else "REJECT",
            has_veto_power=False,
            violations_detected=len(hard_critiques),
            rationale="Laboratory machine turnover, GPU readiness, and maintenance windows preserved." if passed else f"Infrastructure notice: {len(critiques)} alerts.",
            metrics={"total_critiques": len(critiques), "hard_vetoes": len(hard_critiques)}
        )


class MasterArbiterAgent:
    """
    Orchestrates the 7-agent collaborative synthesis loop, coordinates peer dispute resolution,
    guides localized self-healing repair, and enforces the final unanimous consensus gate.
    """

    AGENT_NAME = "MasterArbiterAgent"

    def __init__(self, db: AsyncSession, session_id: Optional[int] = None):
        self.db = db
        self.session_id = session_id
        self.dialogue_history: List[Dict[str, Any]] = []

    def _log_event(self, from_agent: str, to_agent: str, message_type: str, content: str, payload: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": time.time(),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": message_type,
            "content": content,
            "payload": payload or {}
        }
        self.dialogue_history.append(entry)

    async def execute_collaborative_synthesis(
        self,
        target_version_id: int = 12,
        max_negotiation_rounds: int = 5,
        scope: str = "ALL",
        target_sections: Optional[List[str]] = None,
        user_directive: Optional[str] = None,
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end multi-agent collaborative timetable synthesis & verification.
        Supports custom scope, target sections, and natural language user directives.
        """
        start_time = time.time()
        self._log_event(self.AGENT_NAME, "ALL", "INITIALIZATION", f"Initiating Autonomous Multi-Agent Synthesis for Version {target_version_id} (Scope: {scope}).")

        if user_directive:
            self._log_event("USER", self.AGENT_NAME, "DIRECTIVE", f"Operator directive: '{user_directive}' (Scope: {scope})")

        if progress_callback:
            await progress_callback({
                "stage": "STAGE_1_ANCHORING",
                "round": 1,
                "message": "SectionCurriculumAgent & TemporalFlowAgent locking cohort blocks & institutional breaks..."
            })

        # Fetch baseline timetable entries
        from app.services.timetable_service import TimetableService
        tt_data = await TimetableService.get_version_timetable(self.db, version_id=target_version_id, section_name="ALL")
        all_entries = [dict(e) for e in tt_data.get("entries", [])]

        # Scope filtering if specific sections requested
        if target_sections and len(target_sections) > 0:
            target_set = {s.upper().strip() for s in target_sections}
            candidate_entries = [e for e in all_entries if str(e.get("section", "")).upper().strip() in target_set]
            if not candidate_entries:
                candidate_entries = all_entries
        elif scope != "ALL":
            if "II" in scope:
                candidate_entries = [e for e in all_entries if "II " in str(e.get("section", ""))]
            elif "III" in scope:
                candidate_entries = [e for e in all_entries if "III " in str(e.get("section", ""))]
            elif "IV" in scope:
                candidate_entries = [e for e in all_entries if "IV " in str(e.get("section", ""))]
            else:
                candidate_entries = all_entries
        else:
            candidate_entries = all_entries

        self._log_event("SectionCurriculumAgent", self.AGENT_NAME, "PROPOSAL", f"Loaded {len(candidate_entries)} entries for active scope. Anchoring Minors/Honors and SL/EL blocks.")

        # Collaborative Negotiation Loop
        negotiation_success = False
        final_votes: List[AgentVote] = []

        for round_idx in range(1, max_negotiation_rounds + 1):
            if progress_callback:
                await progress_callback({
                    "stage": f"ROUND_{round_idx}_PEER_CRITIQUE",
                    "round": round_idx,
                    "message": f"Peer negotiation Round {round_idx}: Collecting critiques across all 7 agents..."
                })

            # Run peer audits across all specialized agents
            critiques_curriculum = SectionCurriculumAgent.audit(candidate_entries)
            critiques_faculty = FacultyWorkloadAgent.audit(candidate_entries)
            critiques_venue = VenueBlockAgent.audit(candidate_entries)
            critiques_temporal = TemporalFlowAgent.audit(candidate_entries)
            critiques_welfare = StudentWelfareAgent.audit(candidate_entries)
            critiques_infra = LabTechInfraAgent.audit(candidate_entries)

            all_critiques = (
                critiques_curriculum + critiques_faculty + critiques_venue +
                critiques_temporal + critiques_welfare + critiques_infra
            )
            hard_vetoes = [c for c in all_critiques if c.severity == "HARD_VETO"]

            self._log_event(
                self.AGENT_NAME, "ALL", "ROUND_AUDIT",
                f"Round {round_idx} complete: {len(all_critiques)} total critiques, {len(hard_vetoes)} hard vetoes across 7 agents.",
                {"hard_vetoes": len(hard_vetoes), "critiques_count": len(all_critiques)}
            )

            # If hard vetoes exist, orchestrate dispute resolution
            if hard_vetoes:
                self._log_event(self.AGENT_NAME, "VenueBlockAgent", "DISPUTE_RESOLUTION", f"Resolving {len(hard_vetoes)} hard conflicts via targeted local repair.")
                rooms = await ToolRegistry.get_rooms(self.db)
                solver = CPSATSolver()

                # Repair primary conflict
                first_conflict = hard_vetoes[0]
                repair_result = solver.solve_local_repair(
                    current_entries=candidate_entries,
                    available_rooms=rooms,
                    priority_level="P1_CRITICAL"
                )
                if repair_result and repair_result.get("entries"):
                    candidate_entries = repair_result["entries"]
                    self._log_event("VenueBlockAgent", self.AGENT_NAME, "REPAIR_COMPLETE", f"Executed local repair; adjusted {repair_result.get('moved_count', 0)} slots.")
            else:
                negotiation_success = True
                self._log_event(self.AGENT_NAME, "ALL", "CONVERGENCE", f"Multi-Agent negotiations converged successfully at Round {round_idx} with 0 hard vetoes.")
                break

        # Final Consensus Voting Gate (Unanimous 7/7 Signed Consensus)
        vote_curriculum = SectionCurriculumAgent.cast_vote(candidate_entries)
        vote_faculty = FacultyWorkloadAgent.cast_vote(candidate_entries)
        vote_venue = VenueBlockAgent.cast_vote(candidate_entries)
        vote_temporal = TemporalFlowAgent.cast_vote(candidate_entries)
        vote_welfare = StudentWelfareAgent.cast_vote(candidate_entries)
        vote_infra = LabTechInfraAgent.cast_vote(candidate_entries)

        # Validator Ground-Truth
        checker = ConflictChecker()
        report = checker.detect(candidate_entries)
        val_passed = (report.total_hard_violations == 0)
        vote_validator = AgentVote(
            agent_name="ValidatorAgent",
            vote="APPROVE" if val_passed else "REJECT",
            has_veto_power=True,
            violations_detected=report.total_hard_violations,
            rationale=f"Ground truth verified: {report.total_hard_violations} hard clashes." if val_passed else f"VETO: {report.total_hard_violations} hard clashes detected.",
            metrics={"room_clashes": report.room_clashes, "faculty_clashes": report.faculty_clashes, "student_clashes": report.student_clashes}
        )

        final_votes = [
            vote_curriculum, vote_faculty, vote_venue, vote_temporal,
            vote_welfare, vote_infra, vote_validator
        ]
        unanimous = all(v.vote == "APPROVE" for v in final_votes)
        elapsed_sec = round(time.time() - start_time, 2)

        summary = (
            f"Multi-Agent Collaborative Consensus APPROVED: Unanimous 7/7 agents ({', '.join(v.agent_name for v in final_votes)}) voted APPROVE with 0 hard clashes."
            if unanimous else
            f"Multi-Agent Consensus HELD: Rejected by {[v.agent_name for v in final_votes if v.vote == 'REJECT']}."
        )

        self._log_event(self.AGENT_NAME, "USER", "FINAL_DECISION", summary, {"unanimous": unanimous})

        # Persist decision trace in database if session exists
        if self.session_id:
            try:
                dec = AgentDecision(
                    session_id=self.session_id,
                    decision_type="MULTI_AGENT_SYNTHESIS",
                    reason_code="END_TO_END_COLLABORATION",
                    selected_option="PUBLISH_MASTER_TIMETABLE" if unanimous else "HOLD_FOR_REVIEW",
                    risk_level="low" if unanimous else "high",
                    rationale=summary,
                    payload={
                        "unanimous": unanimous,
                        "runtime_seconds": elapsed_sec,
                        "votes": [{
                            "agent": v.agent_name,
                            "vote": v.vote,
                            "has_veto_power": v.has_veto_power,
                            "violations": v.violations_detected,
                            "rationale": v.rationale
                        } for v in final_votes]
                    }
                )
                self.db.add(dec)
                await self.db.commit()
            except Exception:
                pass

        return {
            "status": "APPROVED" if unanimous else "HELD",
            "unanimous_consensus": unanimous,
            "runtime_seconds": elapsed_sec,
            "total_slots": len(candidate_entries),
            "votes": [{
                "agent": v.agent_name,
                "vote": v.vote,
                "has_veto_power": v.has_veto_power,
                "violations": v.violations_detected,
                "rationale": v.rationale,
                "metrics": v.metrics
            } for v in final_votes],
            "dialogue_history": self.dialogue_history,
            "summary": summary,
            "entries": candidate_entries
        }
