from typing import List, Dict, Any, Tuple
from backend.solver.constraints import ConstraintRules


class FitnessEvaluator:
    @staticmethod
    def evaluate(timetable_entries: List[Dict[str, Any]], hard_penalty_weight: int = 10000) -> Dict[str, Any]:
        hard_violations = 0
        soft_penalties = 0

        # SC-01 & SC-02: Faculty daily & weekly workload tracking
        faculty_daily_hours: Dict[Tuple[str, str], int] = {}  # (fac_name, day) -> count
        faculty_weekly_hours: Dict[str, int] = {}
        section_daily_periods: Dict[Tuple[str, str], List[int]] = {}  # (section, day) -> [period list]

        for entry in timetable_entries:
            fac_list = entry.get("faculty_list", [])
            day = entry.get("day", "MON")
            sec = entry.get("section", "")
            period = entry.get("period", 1)

            if sec and period:
                key_sec = (sec, day)
                if key_sec not in section_daily_periods:
                    section_daily_periods[key_sec] = []
                section_daily_periods[key_sec].append(period)

            for fac in fac_list:
                if not fac:
                    continue
                key = (fac, day)
                faculty_daily_hours[key] = faculty_daily_hours.get(key, 0) + 1
                faculty_weekly_hours[fac] = faculty_weekly_hours.get(fac, 0) + 1

        # SC-01: Penalize daily hours > 4
        for (fac, day), hrs in faculty_daily_hours.items():
            if hrs > 4:
                soft_penalties += (hrs - 4) * 30

        # SC-02: Penalize weekly hours > 16 (or rank limit)
        for fac, hrs in faculty_weekly_hours.items():
            max_h = ConstraintRules.get_max_faculty_hours("Assistant Professor")
            if hrs > max_h:
                soft_penalties += (hrs - max_h) * 50

        # SC-03: Student idle gap minimization (gaps between classes on same day)
        for (sec, day), periods in section_daily_periods.items():
            if len(periods) > 1:
                sorted_p = sorted(periods)
                # Count gaps between first and last period that aren't occupied
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

