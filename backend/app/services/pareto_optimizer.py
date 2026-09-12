import time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.timetable_service import TimetableService
try:
    from backend.solver.constraints import ConstraintRules
    from backend.solver.conflict_checker import ConflictChecker
except (ImportError, ModuleNotFoundError):
    from solver.constraints import ConstraintRules
    from solver.conflict_checker import ConflictChecker


class ParetoOptimizer:
    """
    Multi-Objective Pareto Frontier Explorer.
    Evaluates timetable configurations across competing institutional soft constraint objectives:
    1. Faculty Welfare (Workload balance, daily fatigue, free research blocks)
    2. Student Pedagogy (Minimal free gaps, morning theory retention, reduced afternoon load)
    3. Campus Infrastructure & Transit (GPU lab alignment, minimal cross-block sprints)
    """

    PROFILES = {
        "FACULTY_CENTRIC": {
            "name": "Faculty Welfare Focus",
            "description": "Minimizes teacher daily fatigue and balances weekly class distribution.",
            "weights": {"faculty_fatigue": 0.50, "student_gaps": 0.20, "campus_transit": 0.15, "afternoon_load": 0.15}
        },
        "STUDENT_CENTRIC": {
            "name": "Student Pedagogy Focus",
            "description": "Eliminates isolated gaps in student schedules and limits late afternoon fatigue.",
            "weights": {"faculty_fatigue": 0.15, "student_gaps": 0.45, "campus_transit": 0.15, "afternoon_load": 0.25}
        },
        "INFRASTRUCTURE_CENTRIC": {
            "name": "Campus Locality & GPU Focus",
            "description": "Maximizes GPU laboratory matching and clusters classes to prevent campus sprints.",
            "weights": {"faculty_fatigue": 0.15, "student_gaps": 0.15, "campus_transit": 0.50, "afternoon_load": 0.20}
        },
        "BALANCED_CONSENSUS": {
            "name": "Balanced Consensus",
            "description": "Standard multi-agent compromise balancing all stakeholders equally.",
            "weights": {"faculty_fatigue": 0.25, "student_gaps": 0.25, "campus_transit": 0.25, "afternoon_load": 0.25}
        }
    }

    @staticmethod
    def evaluate_objectives(timetable_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Computes the 4 core sub-objective scores (0 to 100, where 100 is best).
        """
        total_slots = max(len(timetable_entries), 1)

        # 1. Faculty Fatigue Score (SC-02)
        fac_daily_hours: Dict[Tuple[str, str], int] = {}
        for e in timetable_entries:
            fac = str(e.get("faculty") or e.get("facultyNames") or "").strip()
            d = str(e.get("day", "")).upper()
            if fac and d:
                fac_daily_hours[(fac, d)] = fac_daily_hours.get((fac, d), 0) + 1

        heavy_days = sum(1 for (fac, d), hrs in fac_daily_hours.items() if hrs >= 5)
        faculty_fatigue_score = max(0.0, 100.0 - (heavy_days * 3.5))

        # 2. Student Gap Compactness (SC-03)
        sec_day_slots: Dict[Tuple[str, str], set] = {}
        for e in timetable_entries:
            sec = str(e.get("section") or "")
            d = str(e.get("day", "")).upper()
            p = int(e.get("period", 1))
            if sec and d:
                sec_day_slots.setdefault((sec, d), set()).add(p)

        isolated_gaps = 0
        for (sec, d), periods in sec_day_slots.items():
            if len(periods) >= 2:
                for p in range(min(periods) + 1, max(periods)):
                    if p not in periods:
                        isolated_gaps += 1

        student_gap_score = max(0.0, 100.0 - (isolated_gaps * 1.5))

        # 3. Campus Locality & Transit Score (SC-09)
        transit_audit = ConstraintRules.calculate_block_transit_score(timetable_entries)
        cross_block_sprints = transit_audit.get("cross_block_sprints", 0)
        campus_transit_score = max(0.0, 100.0 - (cross_block_sprints * 2.0))

        # 4. Afternoon Load Optimization (SC-07: P7-P8 ratio <= 40%)
        p78_slots = sum(1 for e in timetable_entries if int(e.get("period", 1)) in (7, 8))
        late_ratio = (p78_slots / total_slots) * 100.0
        afternoon_load_score = max(0.0, 100.0 - max(0.0, (late_ratio - 25.0) * 2.5))

        return {
            "faculty_fatigue_score": round(faculty_fatigue_score, 1),
            "student_gap_score": round(student_gap_score, 1),
            "campus_transit_score": round(campus_transit_score, 1),
            "afternoon_load_score": round(afternoon_load_score, 1),
            "raw_metrics": {
                "heavy_faculty_days": heavy_days,
                "isolated_student_gaps": isolated_gaps,
                "cross_block_sprints": cross_block_sprints,
                "late_afternoon_pct": round(late_ratio, 1)
            }
        }

    @staticmethod
    def compute_composite_profile_scores(objectives: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies profile weights to produce composite fitness ratings across the 4 profiles.
        """
        f_score = objectives["faculty_fatigue_score"]
        s_score = objectives["student_gap_score"]
        t_score = objectives["campus_transit_score"]
        a_score = objectives["afternoon_load_score"]

        profile_scores = {}
        for p_key, p_meta in ParetoOptimizer.PROFILES.items():
            w = p_meta["weights"]
            composite = (
                (f_score * w["faculty_fatigue"]) +
                (s_score * w["student_gaps"]) +
                (t_score * w["campus_transit"]) +
                (a_score * w["afternoon_load"])
            )
            profile_scores[p_key] = {
                "name": p_meta["name"],
                "description": p_meta["description"],
                "composite_score": round(composite, 1)
            }

        return profile_scores

    @staticmethod
    async def evaluate_timetable(
        db: AsyncSession,
        version_id: int = 5,
        candidate_entries: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates the target timetable or candidate against multi-objective Pareto dimensions.
        """
        start_time = time.time()
        if not candidate_entries:
            tt_res = await TimetableService.get_version_timetable(db, version_id=version_id, section_name="ALL")
            entries = tt_res.get("entries", [])
        else:
            entries = candidate_entries

        checker = ConflictChecker()
        clash_report = checker.detect(entries)

        objectives = ParetoOptimizer.evaluate_objectives(entries)
        profile_scores = ParetoOptimizer.compute_composite_profile_scores(objectives)

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "version_id": version_id,
            "total_slots": len(entries),
            "hard_violations": clash_report.total_hard_violations,
            "is_feasible": clash_report.total_hard_violations == 0,
            "objectives": objectives,
            "profile_scores": profile_scores,
            "execution_time_ms": elapsed_ms
        }
