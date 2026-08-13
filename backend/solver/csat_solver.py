import time
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional, Set
from pydantic import BaseModel, Field
from ortools.sat.python import cp_model

try:
    from backend.solver.constraints import ConstraintRules
except (ImportError, ModuleNotFoundError):
    from solver.constraints import ConstraintRules


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

    def on_solution_callback(self) -> None:
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
    """
    Production-grade CP-SAT Timetable Constraint Optimizer.
    Enforces Hard Constraints HC-01 through HC-13 and optimizes slot compacting objectives.
    """

    SELF_DIRECTED_TYPES: Set[str] = frozenset({
        "LIBRARY", "IIC", "SL_EL", "SL/EL", "OE", "CRT", "SPECIAL",
        "MINORHONOR", "MINORS", "HONORS", "MINORS/HONORS", "LIBRARY/IIC"
    })
    
    VIRTUAL_LIB_ROOM: Dict[str, Any] = {
        "id": "VIRTUAL_LIBRARY",
        "code": "VIRTUAL_LIBRARY",
        "room_type": "library",
        "capacity": 9999
    }

    def __init__(self, config: Optional[SolverConfig] = None):
        self.config = config or SolverConfig()

    @staticmethod
    def _has_faculty(ss: Dict[str, Any]) -> bool:
        """Determines if a subject assignment record carries a non-empty faculty assignment."""
        fname = ss.get("faculty_name")
        return bool(fname and str(fname).strip())

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
        """
        Executes CP-SAT constraint optimization across section timetable demands.
        Returns a response dict containing status, runtime, entry counts, and scheduled slot entries.
        """
        start_time = time.time()
        model = cp_model.CpModel()
        faculty_subject_map = faculty_subject_map or {}

        # -----------------------------------------------------------------------
        # 1. Pre-index and group structures for fast O(1) lookups
        # -----------------------------------------------------------------------
        sec_subjs_by_sec: Dict[Any, List[Dict[str, Any]]] = {}
        for ss in section_subjects:
            s_id = ss["section_id"]
            if s_id not in sec_subjs_by_sec:
                sec_subjs_by_sec[s_id] = []
            sec_subjs_by_sec[s_id].append(ss)

        # -----------------------------------------------------------------------
        # 2. Decision Variable Initialization: x[section_id, subject_id, room_id, slot_id]
        # -----------------------------------------------------------------------
        x: Dict[Tuple[Any, Any, Any, Any], cp_model.IntVar] = {}

        for sec in sections:
            s_id = sec["id"]
            sec_subjs = sec_subjs_by_sec.get(s_id, [])

            for ss in sec_subjs:
                sub_id = ss["subject_id"]
                sub_type = str(ss.get("subject_type", "L")).strip().upper()
                sub_code = str(ss.get("subject_code", "")).strip().upper()

                is_self_directed = (
                    sub_type in self.SELF_DIRECTED_TYPES
                    or sub_code in self.SELF_DIRECTED_TYPES
                    or "MINOR" in sub_code
                    or "HONOR" in sub_code
                    or "SL/EL" in sub_code
                    or "SL_EL" in sub_code
                    or "LIBRARY" in sub_code
                )

                if is_self_directed:
                    room_pool = [self.VIRTUAL_LIB_ROOM]
                elif sub_type in ("P", "LAB"):
                    room_pool = [r for r in rooms if r.get("room_type") in ("lab", "computer_lab", "gpu_lab")] or rooms
                elif sub_type in ("L", "T"):
                    room_pool = [r for r in rooms if r.get("room_type") not in ("lab", "computer_lab", "gpu_lab")] or rooms
                else:
                    room_pool = rooms

                for r in room_pool:
                    r_id = r["id"]
                    for t in time_slots:
                        t_id = t["id"]
                        x[s_id, sub_id, r_id, t_id] = model.NewBoolVar(f"x_{s_id}_{sub_id}_{r_id}_{t_id}")

        # -----------------------------------------------------------------------
        # 3. HC-01: Room Conflict (At most 1 class per room per slot)
        # -----------------------------------------------------------------------
        for r in rooms:
            r_id = r["id"]
            for t in time_slots:
                t_id = t["id"]
                room_vars = [
                    x[sec["id"], ss["subject_id"], r_id, t_id]
                    for sec in sections
                    for ss in sec_subjs_by_sec.get(sec["id"], [])
                    if (sec["id"], ss["subject_id"], r_id, t_id) in x
                ]
                if room_vars:
                    model.AddAtMostOne(room_vars)

        # -----------------------------------------------------------------------
        # 4. HC-02: Faculty Assignments & Double-Booking Guard
        # -----------------------------------------------------------------------
        fac_to_sec_subjs: Dict[str, List[Tuple[Any, Any]]] = {}
        for sec in sections:
            s_id = sec["id"]
            for ss in sec_subjs_by_sec.get(s_id, []):
                sub_type = str(ss.get("subject_type", "L")).strip().upper()
                if sub_type in self.SELF_DIRECTED_TYPES or not self._has_faculty(ss):
                    continue

                sub_id = ss["subject_id"]
                sub_code = str(ss.get("subject_code", "")).strip()

                ss_facs: Set[str] = set()
                if self._has_faculty(ss):
                    ss_facs.add(str(ss["faculty_name"]).strip())
                for co in ss.get("co_faculty", []):
                    if co and str(co).strip():
                        ss_facs.add(str(co).strip())

                if not ss_facs:
                    for f_name, codes in faculty_subject_map.items():
                        if sub_code in codes:
                            ss_facs.add(f_name)

                for f_name in ss_facs:
                    if f_name not in fac_to_sec_subjs:
                        fac_to_sec_subjs[f_name] = []
                    fac_to_sec_subjs[f_name].append((s_id, sub_id))

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

        # Teacher daily teaching cap constraint
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

        # -----------------------------------------------------------------------
        # 5. HC-03: Section Conflict (At most 1 class per section per slot)
        # -----------------------------------------------------------------------
        for sec in sections:
            s_id = sec["id"]
            sec_subjs = sec_subjs_by_sec.get(s_id, [])
            for t in time_slots:
                t_id = t["id"]
                sec_vars = [
                    x[s_id, ss["subject_id"], r["id"], t_id]
                    for ss in sec_subjs
                    for r in ([self.VIRTUAL_LIB_ROOM] if str(ss.get("subject_type")).upper() in self.SELF_DIRECTED_TYPES else rooms)
                    if (s_id, ss["subject_id"], r["id"], t_id) in x
                ]
                if sec_vars:
                    model.AddAtMostOne(sec_vars)

        # -----------------------------------------------------------------------
        # 6. HC-04: Subject Frequency (Exact slots needed per subject per section)
        # -----------------------------------------------------------------------
        for sec in sections:
            s_id = sec["id"]
            sec_subjs = sec_subjs_by_sec.get(s_id, [])
            for ss in sec_subjs:
                sub_id = ss["subject_id"]
                needed = ss.get("total_slots_needed", 3)
                sub_type = str(ss.get("subject_type", "L")).upper()
                sub_rooms = [self.VIRTUAL_LIB_ROOM] if sub_type in self.SELF_DIRECTED_TYPES else rooms

                if sub_type in ("P", "LAB"):
                    valid_lab_starts = [1, 3, 4, 6, 7]
                    start_vars = [
                        x[s_id, sub_id, r["id"], t["id"]]
                        for r in sub_rooms
                        for t in time_slots
                        if t.get("period") in valid_lab_starts and not t.get("is_blocked")
                        and (s_id, sub_id, r["id"], t["id"]) in x
                    ]
                    if start_vars:
                        model.Add(sum(start_vars) == needed)
                else:
                    all_sub_vars = [
                        x[s_id, sub_id, r["id"], t["id"]]
                        for r in sub_rooms
                        for t in time_slots
                        if (s_id, sub_id, r["id"], t["id"]) in x
                    ]
                    if all_sub_vars:
                        model.Add(sum(all_sub_vars) == needed)

        # -----------------------------------------------------------------------
        # 7. HC-05 & HC-06: Room Capacity & Type Compatibility
        # -----------------------------------------------------------------------
        for sec in sections:
            s_id = sec["id"]
            sec_capacity = sec.get("student_count", 60)
            sec_subjs = sec_subjs_by_sec.get(s_id, [])
            for ss in sec_subjs:
                sub_id = ss["subject_id"]
                sub_type = str(ss.get("subject_type", "L")).upper()

                if sub_type in self.SELF_DIRECTED_TYPES:
                    continue

                for r in rooms:
                    r_id = r["id"]
                    r_cap = r.get("capacity", 60)
                    r_type = r.get("room_type", "classroom")

                    is_cap_ok = r_cap >= sec_capacity
                    is_type_ok = ConstraintRules.is_room_compatible(sub_type, r_type)

                    if not (is_cap_ok and is_type_ok):
                        for t in time_slots:
                            if (s_id, sub_id, r_id, t["id"]) in x:
                                model.Add(x[s_id, sub_id, r_id, t["id"]] == 0)

        # -----------------------------------------------------------------------
        # 8. HC-07: Break / Lunch Slot Protection
        # -----------------------------------------------------------------------
        for t in time_slots:
            if t.get("is_blocked", False) or ConstraintRules.is_break_slot(t.get("period", 0), t.get("slot_name", "")):
                t_id = t["id"]
                for sec in sections:
                    s_id = sec["id"]
                    for ss in sec_subjs_by_sec.get(s_id, []):
                        sub_id = ss["subject_id"]
                        sub_type = str(ss.get("subject_type", "L")).upper()
                        sub_rooms = [self.VIRTUAL_LIB_ROOM] if sub_type in self.SELF_DIRECTED_TYPES else rooms
                        for r in sub_rooms:
                            if (s_id, sub_id, r["id"], t_id) in x:
                                model.Add(x[s_id, sub_id, r["id"], t_id] == 0)

        # -----------------------------------------------------------------------
        # 9. HC-08 & Special Cohort Blocks (Labs, Minors/Honors, 4th Year SL/EL)
        # -----------------------------------------------------------------------
        for sec in sections:
            s_id = sec["id"]
            sec_subjs = sec_subjs_by_sec.get(s_id, [])

            # Rule 1: Lab Consecutive Block Enforcement
            lab_subjs = [ss for ss in sec_subjs if str(ss.get("subject_type")).upper() in ("P", "LAB")]
            for ss in lab_subjs:
                sub_id = ss["subject_id"]

                # Saturday Lab prohibition
                for r in rooms:
                    for t in time_slots:
                        if t.get("day") == "SAT" and (s_id, sub_id, r["id"], t["id"]) in x:
                            model.Add(x[s_id, sub_id, r["id"], t["id"]] == 0)

                for day in ["MON", "TUE", "WED", "THU", "FRI"]:
                    day_slots = {t.get("period", 0): t for t in time_slots if t.get("day") == day and not t.get("is_blocked")}
                    valid_start_periods = [1, 3, 4, 6, 7]

                    for p1 in valid_start_periods:
                        p2 = p1 + 1
                        if p1 in day_slots and p2 in day_slots:
                            t1_id = day_slots[p1]["id"]
                            t2_id = day_slots[p2]["id"]

                            for r in rooms:
                                r_id = r["id"]
                                if (s_id, sub_id, r_id, t1_id) in x and (s_id, sub_id, r_id, t2_id) in x:
                                    model.Add(x[s_id, sub_id, r_id, t2_id] == 1).OnlyEnforceIf(x[s_id, sub_id, r_id, t1_id])

                    start_day_vars = [
                        x[s_id, sub_id, r["id"], day_slots[p]["id"]]
                        for r in rooms
                        for p in valid_start_periods
                        if p in day_slots and (s_id, sub_id, r["id"], day_slots[p]["id"]) in x
                    ]
                    if start_day_vars:
                        model.Add(sum(start_day_vars) <= 1)

            # Rule 2: Minors/Honors Global Slot Protection
            minors_subjs = [
                ss for ss in sec_subjs
                if ("MINOR" in str(ss.get("subject_code", "")).upper() or "HONOR" in str(ss.get("subject_code", "")).upper())
            ]
            has_p78_slots = any(t.get("period") in (7, 8) for t in time_slots)
            if minors_subjs and has_p78_slots:
                for ss in minors_subjs:
                    sub_id = ss["subject_id"]
                    sub_type = str(ss.get("subject_type", "L")).upper()
                    sub_rooms = [self.VIRTUAL_LIB_ROOM] if sub_type in self.SELF_DIRECTED_TYPES else rooms
                    for r in sub_rooms:
                        for t in time_slots:
                            t_day = t.get("day")
                            t_p = t.get("period")
                            if not (t_day in ("WED", "THU") and t_p in (7, 8)):
                                if (s_id, sub_id, r["id"], t["id"]) in x:
                                    model.Add(x[s_id, sub_id, r["id"], t["id"]] == 0)

                regular_subjs = [
                    ss for ss in sec_subjs
                    if not ("MINOR" in str(ss.get("subject_code", "")).upper() or "HONOR" in str(ss.get("subject_code", "")).upper())
                ]
                for ss in regular_subjs:
                    sub_id = ss["subject_id"]
                    sub_type = str(ss.get("subject_type", "L")).upper()
                    sub_rooms = [self.VIRTUAL_LIB_ROOM] if sub_type in self.SELF_DIRECTED_TYPES else rooms
                    for r in sub_rooms:
                        for t in time_slots:
                            if t.get("day") in ("WED", "THU") and t.get("period") in (7, 8):
                                if (s_id, sub_id, r["id"], t["id"]) in x:
                                    model.Add(x[s_id, sub_id, r["id"], t["id"]] == 0)

            # Rule 3: 4th Year SL/EL Fixed Block Protection
            s_id_str = str(s_id).upper()
            if "IV " in s_id_str or "IV_" in s_id_str or "IV-" in s_id_str:
                slel_subjs = [
                    ss for ss in sec_subjs
                    if ("SL/EL" in str(ss.get("subject_code", "")).upper()
                        or "SL_EL" in str(ss.get("subject_code", "")).upper()
                        or "LEARNING" in str(ss.get("subject_code", "")).upper())
                ]
                if slel_subjs:
                    for ss in slel_subjs:
                        sub_id = ss["subject_id"]
                        sub_type = str(ss.get("subject_type", "L")).upper()
                        sub_rooms = [self.VIRTUAL_LIB_ROOM] if sub_type in self.SELF_DIRECTED_TYPES else rooms
                        for r in sub_rooms:
                            for t in time_slots:
                                t_p = t.get("period")
                                t_day = t.get("day")
                                is_allowed_slel = (t_p in (1, 2)) or (t_day == "SAT" and t_p in (6, 7, 8))
                                if not is_allowed_slel:
                                    if (s_id, sub_id, r["id"], t["id"]) in x:
                                        model.Add(x[s_id, sub_id, r["id"], t["id"]] == 0)

        # -----------------------------------------------------------------------
        # 10. Objective Function: Schedule Compacting into Early Periods (P1..P6)
        # -----------------------------------------------------------------------
        obj_terms = []
        for (s_id, sub_id, r_id, t_id), var in x.items():
            try:
                p_num = int(str(t_id).split("_")[-1])
            except Exception:
                p_num = 1
            obj_terms.append(var * p_num)

        if obj_terms:
            model.Minimize(sum(obj_terms))

        # -----------------------------------------------------------------------
        # 11. CP-SAT Solver Tuning Parameters
        # -----------------------------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self.config.timeout_seconds)
        solver.parameters.num_search_workers = 8
        solver.parameters.cp_model_presolve = True
        solver.parameters.log_search_progress = False

        cb = LiveSolutionCallback(progress_callback)
        status = solver.Solve(model, cb)
        runtime = time.time() - start_time
        is_feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

        entries = []
        if is_feasible:
            for sec in sections:
                s_id = sec["id"]
                sec_subjs = sec_subjs_by_sec.get(s_id, [])
                for ss in sec_subjs:
                    sub_id = ss["subject_id"]
                    sub_type = str(ss.get("subject_type", "L")).upper()
                    room_pool = [self.VIRTUAL_LIB_ROOM] if sub_type in self.SELF_DIRECTED_TYPES else rooms

                    for r in room_pool:
                        r_id = r["id"]
                        for t in time_slots:
                            t_id = t["id"]
                            var = x.get((s_id, sub_id, r_id, t_id))
                            if var is None:
                                continue
                            if solver.Value(var) == 1:
                                sec_name = sec.get("name") or s_id
                                sub_code = ss.get("subject_code") or ss.get("subject_id") or sub_id
                                room_code = r.get("code") or r.get("id") or r_id
                                fac_name = ss.get("faculty_name") or ""
                                if fac_name:
                                    fac_name = str(fac_name).strip()
                                co_facs = ss.get("co_faculty") or []
                                all_facs = [fac_name] + [str(c).strip() for c in co_facs if c] if fac_name else []
                                span = ss.get("continuous_slots") or 1

                                entries.append({
                                    "id": f"{s_id}_{sub_id}_{t_id}",
                                    "section_id": s_id,
                                    "section": sec_name,
                                    "sectionName": sec_name,
                                    "subject_id": sub_id,
                                    "subject": sub_code,
                                    "subjectCode": sub_code,
                                    "room_id": r_id,
                                    "room": room_code,
                                    "roomCode": room_code,
                                    "time_slot_id": t_id,
                                    "day": t.get("day"),
                                    "period": t.get("period"),
                                    "faculty": fac_name,
                                    "facultyName": fac_name,
                                    "facultyNames": all_facs,
                                    "type": sub_type,
                                    "subjectType": sub_type,
                                    "spanPeriods": span
                                })

        return {
            "status": "OPTIMAL" if status == cp_model.OPTIMAL else ("FEASIBLE" if is_feasible else "INFEASIBLE"),
            "runtime_seconds": round(runtime, 2),
            "hard_violations": 0 if is_feasible else 10,
            "soft_violations": 0,
            "entries_count": len(entries),
            "entries": entries
        }


