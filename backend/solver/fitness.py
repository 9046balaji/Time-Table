from typing import List, Dict, Any, Tuple, Set, Optional
from backend.solver.constraints import ConstraintRules
from backend.solver.conflict_checker import ConflictChecker


class FitnessEvaluator:
    """
    Evaluates timetable fitness scores based on hard constraint violations 
    and soft penalty deductions (SC-01: Faculty Daily Load, SC-02: Faculty Weekly Cap, SC-03: Student Idle Gaps).
    """

    _checker: ConflictChecker = ConflictChecker()

    @classmethod
    def evaluate(cls, timetable_entries: List[Dict[str, Any]], hard_penalty_weight: int = 10000) -> Dict[str, Any]:
        """
        Calculates fitness score for a given timetable candidate variant.
        Returns a dict containing overall fitness score, hard violation counts, and soft penalty details.
        """
        # 1. Audit hard violations using ConflictChecker
        clash_report = cls._checker.detect(timetable_entries)
        hard_violations = clash_report.total_hard_violations
        soft_penalties = 0

        # 2. Track Soft Constraints (SC-01, SC-02, SC-03)
        faculty_daily_hours: Dict[Tuple[str, str], int] = {}
        faculty_weekly_hours: Dict[str, int] = {}
        section_daily_periods: Dict[Tuple[str, str], List[int]] = {}

        for entry in timetable_entries:
            if isinstance(entry, dict):
                fac_list = entry.get("faculty_list") or entry.get("faculty") or []
                day = ConstraintRules.normalize_string(entry.get("day", "MON"))
                sec = str(entry.get("section", "")).strip()
                period = int(entry.get("period", 1) or 1)
            else:
                fac_list = getattr(entry, "faculty_list", []) or getattr(entry, "faculty", [])
                day = ConstraintRules.normalize_string(getattr(entry, "day", "MON"))
                sec = str(getattr(entry, "section", "")).strip()
                period = int(getattr(entry, "period", 1) or 1)

            if isinstance(fac_list, str):
                fac_list = [f.strip() for f in fac_list.split(",") if f.strip()]

            if sec and period > 0:
                key_sec = (sec, day)
                if key_sec not in section_daily_periods:
                    section_daily_periods[key_sec] = []
                section_daily_periods[key_sec].append(period)

            for fac in fac_list:
                f_clean = str(fac).strip()
                if not f_clean or f_clean.upper() in ("", "NONE", "UNDEFINED"):
                    continue
                key_fac = (f_clean, day)
                faculty_daily_hours[key_fac] = faculty_daily_hours.get(key_fac, 0) + 1
                faculty_weekly_hours[f_clean] = faculty_weekly_hours.get(f_clean, 0) + 1

        # SC-01: Penalize faculty daily hours > 4
        for (fac, day), hrs in faculty_daily_hours.items():
            if hrs > 4:
                soft_penalties += (hrs - 4) * 30

        # SC-02: Penalize faculty weekly hours > rank maximum cap
        max_h = ConstraintRules.get_max_faculty_hours("Assistant Professor")
        for fac, hrs in faculty_weekly_hours.items():
            if hrs > max_h:
                soft_penalties += (hrs - max_h) * 50

        # SC-03: Student idle gap penalty (gaps between classes on same day)
        for (sec, day), periods in section_daily_periods.items():
            if len(periods) > 1:
                sorted_p = sorted(periods)
                span = sorted_p[-1] - sorted_p[0] + 1
                gaps = span - len(sorted_p)
                if gaps > 0:
                    soft_penalties += gaps * 20

        total_fitness = -(hard_violations * hard_penalty_weight + soft_penalties)

        return {
            "fitness_score": total_fitness,
            "hard_violations": hard_violations,
            "soft_violations": soft_penalties // 10,
            "soft_penalty_points": soft_penalties
        }


