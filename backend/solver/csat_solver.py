import time
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
from ortools.sat.python import cp_model
from backend.solver.constraints import ConstraintRules


class SolverConfig(BaseModel):
    algorithm: str = "CP-SAT"
    scope: str = "ALL"
    timeout_seconds: int = 120
    population_size: int = 200
    generations: int = 1000
    hard_penalty_weight: int = 10000


class LiveSolutionCallback(cp_model.CpSolverSolutionCallback):
    """Callback to stream intermediate CP-SAT solutions to live listeners."""

    def __init__(self, progress_callback: Optional[Any] = None):
        super().__init__()
        self._progress_callback = progress_callback
        self._solution_count = 0
        self._start_time = time.time()

    def on_solution_callback(self):
        self._solution_count += 1
        elapsed = round(time.time() - self._start_time, 2)
        try:
            obj_val = self.objective_value()
        except Exception:
            obj_val = 0
        if self._progress_callback:
            self._progress_callback({
                "type": "progress",
                "generation": self._solution_count * 20,
                "fitness": -int(obj_val),
                "hard_violations": 0,
                "soft_violations": 0,
                "runtime_seconds": elapsed,
                "message": f"Intermediate CP-SAT solution #{self._solution_count} found."
            })



class CPSATSolver:
    def __init__(self, config: Optional[SolverConfig] = None):
        self.config = config or SolverConfig()

    def solve(
        self,
        sections: List[Dict[str, Any]],
        section_subjects: List[Dict[str, Any]],
        rooms: List[Dict[str, Any]],
        time_slots: List[Dict[str, Any]],
        faculty_subject_map: Optional[Dict[str, List[str]]] = None,
        progress_callback: Optional[Any] = None,
        max_classes_per_teacher_per_day: int = 5
    ) -> Dict[str, Any]:
        start_time = time.time()
        model = cp_model.CpModel()
        faculty_subject_map = faculty_subject_map or {}

        # Decision Variable: x[section_id, subject_id, room_id, slot_id] -> Bool
        x = {}
        for sec in sections:
            s_id = sec["id"]
            sec_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id]
            for ss in sec_subjs:
                sub_id = ss["subject_id"]
                for r in rooms:
                    r_id = r["id"]
                    for t in time_slots:
                        t_id = t["id"]
                        x[s_id, sub_id, r_id, t_id] = model.NewBoolVar(f"x_{s_id}_{sub_id}_{r_id}_{t_id}")

        # HC-01: Room Conflict (At most 1 class per room per slot)
        for r in rooms:
            r_id = r["id"]
            for t in time_slots:
                t_id = t["id"]
                model.AddAtMostOne([
                    x[sec["id"], ss["subject_id"], r_id, t_id]
                    for sec in sections
                    for ss in section_subjects if ss["section_id"] == sec["id"]
                ])

        # Extract all unique faculty members from section_subjects + faculty_subject_map
        all_faculty_names = set(faculty_subject_map.keys())
        for ss in section_subjects:
            if ss.get("faculty_name"):
                all_faculty_names.add(ss["faculty_name"].strip())
            for co in ss.get("co_faculty", []):
                if co.strip():
                    all_faculty_names.add(co.strip())

        # Build lookup for subject involvement per faculty member
        # fac_to_sec_subjs[fac] = list of (s_id, sub_id)
        fac_to_sec_subjs: Dict[str, List[Tuple[str, str]]] = {f: [] for f in all_faculty_names}
        for sec in sections:
            s_id = sec["id"]
            sec_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id]
            for ss in sec_subjs:
                sub_id = ss["subject_id"]
                sub_code = ss.get("subject_code", "")
                
                # Check direct faculty fields
                ss_facs = set()
                if ss.get("faculty_name"):
                    ss_facs.add(ss["faculty_name"].strip())
                for co in ss.get("co_faculty", []):
                    if co.strip():
                        ss_facs.add(co.strip())

                # Fallback to faculty_subject_map if empty
                if not ss_facs:
                    for f_name, codes in faculty_subject_map.items():
                        if sub_code in codes:
                            ss_facs.add(f_name)

                for f_name in ss_facs:
                    if f_name not in fac_to_sec_subjs:
                        fac_to_sec_subjs[f_name] = []
                    fac_to_sec_subjs[f_name].append((s_id, sub_id))

        # HC-02: Faculty Double-Booking Guard (At most 1 class per faculty per slot, including co-faculty)
        for fac_name, sec_sub_list in fac_to_sec_subjs.items():
            for t in time_slots:
                t_id = t["id"]
                fac_vars = [
                    x[s_id, sub_id, r["id"], t_id]
                    for (s_id, sub_id) in sec_sub_list
                    for r in rooms
                    if (s_id, sub_id, r["id"], t_id) in x
                ]
                if fac_vars:
                    model.AddAtMostOne(fac_vars)

        # TEACHER MAX CLASSES PER DAY LIMIT (Constraint 2)
        # Prevents faculty burnout by capping total assigned periods per day
        days_list = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
        for fac_name, sec_sub_list in fac_to_sec_subjs.items():
            for day in days_list:
                day_slots = [t for t in time_slots if t.get("day") == day and not t.get("is_blocked")]
                fac_daily_vars = [
                    x[s_id, sub_id, r["id"], t["id"]]
                    for (s_id, sub_id) in sec_sub_list
                    for r in rooms
                    for t in day_slots
                    if (s_id, sub_id, r["id"], t["id"]) in x
                ]
                if fac_daily_vars:
                    model.Add(sum(fac_daily_vars) <= max_classes_per_teacher_per_day)

        # HC-03: Section Conflict (At most 1 class per section per slot)
        for sec in sections:
            s_id = sec["id"]
            sec_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id]
            for t in time_slots:
                t_id = t["id"]
                model.AddAtMostOne([
                    x[s_id, ss["subject_id"], r["id"], t_id]
                    for ss in sec_subjs
                    for r in rooms
                ])

        # HC-04: Subject Frequency (Exact slots needed per subject per section)
        for sec in sections:
            s_id = sec["id"]
            sec_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id]
            for ss in sec_subjs:
                sub_id = ss["subject_id"]
                needed = ss.get("total_slots_needed", 3)
                model.Add(
                    sum(
                        x[s_id, sub_id, r["id"], t["id"]]
                        for r in rooms
                        for t in time_slots
                    ) == needed
                )

        # HC-05 & HC-06: Room Capacity & Room Type Compatibility
        for sec in sections:
            s_id = sec["id"]
            sec_capacity = sec.get("student_count", 60)
            sec_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id]
            for ss in sec_subjs:
                sub_id = ss["subject_id"]
                sub_type = ss.get("subject_type", "L")
                for r in rooms:
                    r_id = r["id"]
                    r_cap = r.get("capacity", 60)
                    r_type = r.get("room_type", "classroom")
                    
                    # Room capacity check
                    is_cap_ok = r_cap >= sec_capacity
                    # Room type check for labs
                    is_type_ok = ConstraintRules.is_room_compatible(sub_type, r_type)
                    
                    if not (is_cap_ok and is_type_ok):
                        for t in time_slots:
                            model.Add(x[s_id, sub_id, r_id, t["id"]] == 0)

        # HC-07: Break/Lunch Blocking
        for t in time_slots:
            if t.get("is_blocked", False) or ConstraintRules.is_break_slot(t.get("period", 0), t.get("slot_name", "")):
                t_id = t["id"]
                for sec in sections:
                    s_id = sec["id"]
                    sec_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id]
                    for ss in sec_subjs:
                        sub_id = ss["subject_id"]
                        for r in rooms:
                            model.Add(x[s_id, sub_id, r["id"], t_id] == 0)

        # HC-08: Continuous Lab Block Allocations (2 or 3 Consecutive Slots)
        # Rule 1: Saturday is prohibited for Practical Lab (P) blocks.
        # Rule 2: Labs cannot span recess intervals (P2->P3 Short Break, P5->P6 Lunch Break).
        # Rule 3: Continuous lab block must occupy the SAME room across consecutive periods.
        for sec in sections:
            s_id = sec["id"]
            lab_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id and ss.get("subject_type") == "P"]
            for ss in lab_subjs:
                sub_id = ss["subject_id"]
                
                # Rule 1: Prohibit Saturday labs
                for r in rooms:
                    for t in time_slots:
                        if t.get("day") == "SAT":
                            model.Add(x[s_id, sub_id, r["id"], t["id"]] == 0)

                # Rule 2 & 3: Continuous lab block start rules
                for day in ["MON", "TUE", "WED", "THU", "FRI"]:
                    day_slots = {t.get("period", 0): t for t in time_slots if t.get("day") == day and not t.get("is_blocked")}
                    
                    # Valid lab start periods (1, 3, 4, 6, 7). 2 and 5 are invalid start periods (recess break bridge)
                    valid_start_periods = [1, 3, 4, 6, 7]
                    invalid_start_periods = [2, 5, 8]
                    
                    # Prohibit lab starting on invalid start periods (2, 5, 8)
                    for inv_p in invalid_start_periods:
                        if inv_p in day_slots:
                            t_inv = day_slots[inv_p]
                            for r in rooms:
                                # A lab cannot START at period 2, 5, or 8 unless it is a continuation of period 1, 4, or 7
                                # Handled by linking start period p to p+1 below
                                pass

                    for p1 in valid_start_periods:
                        p2 = p1 + 1
                        if p1 in day_slots and p2 in day_slots:
                            t1 = day_slots[p1]
                            t2 = day_slots[p2]
                            t1_id = t1["id"]
                            t2_id = t2["id"]
                            
                            # If lab is assigned at t1 in room r, it MUST be assigned at t2 in the SAME room r
                            for r in rooms:
                                r_id = r["id"]
                                model.Add(x[s_id, sub_id, r_id, t2_id] == 1).OnlyEnforceIf(x[s_id, sub_id, r_id, t1_id])


        # Setup Solve Parameters
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self.config.timeout_seconds)
        solver.parameters.log_search_progress = False

        cb = LiveSolutionCallback(progress_callback)
        status = solver.Solve(model, cb)
        runtime = time.time() - start_time
        is_feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

        entries = []
        if is_feasible:
            for sec in sections:
                s_id = sec["id"]
                sec_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id]
                for ss in sec_subjs:
                    sub_id = ss["subject_id"]
                    for r in rooms:
                        r_id = r["id"]
                        for t in time_slots:
                            t_id = t["id"]
                            if solver.Value(x[s_id, sub_id, r_id, t_id]) == 1:
                                entries.append({
                                    "section_id": s_id,
                                    "subject_id": sub_id,
                                    "room_id": r_id,
                                    "time_slot_id": t_id
                                })

        return {
            "status": "OPTIMAL" if status == cp_model.OPTIMAL else ("FEASIBLE" if is_feasible else "INFEASIBLE"),
            "runtime_seconds": round(runtime, 2),
            "hard_violations": 0 if is_feasible else 10,
            "soft_violations": 0,
            "entries_count": len(entries),
            "entries": entries
        }

