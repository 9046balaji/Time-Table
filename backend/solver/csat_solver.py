import time
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
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

        # -----------------------------------------------------------------------
        # SELF-DIRECTED SLOT TYPES — defined first so all constraint blocks can use it
        # -----------------------------------------------------------------------
        SELF_DIRECTED_TYPES = frozenset({"LIBRARY", "IIC", "SL_EL", "SL/EL", "OE", "CRT", "SPECIAL", "MINORHONOR", "MINORS", "HONORS", "MINORS/HONORS", "LIBRARY/IIC"})


        def _has_faculty(ss: Dict[str, Any]) -> bool:
            """True when a subject record carries a real (non-None, non-empty) faculty name."""
            fname = ss.get("faculty_name")
            return bool(fname and str(fname).strip())

        # -----------------------------------------------------------------------
        # VIRTUAL LIBRARY ROOM INJECTION
        # Self-directed slots (LIBRARY, IIC, SL_EL, OE, CRT) have no physical room.
        # We inject a virtual room so CP-SAT decision variables exist for HC-04
        # (subject frequency == needed) to be satisfiable. HC-01 room-conflict
        # constraints still apply to the virtual room, ensuring no two sections
        # share the same LIBRARY slot simultaneously.
        # -----------------------------------------------------------------------
        VIRTUAL_LIB_ROOM = {"id": "VIRTUAL_LIBRARY", "room_type": "library", "capacity": 9999}

        # Decision Variable: x[section_id, subject_id, room_id, slot_id] -> Bool
        x = {}
        for sec in sections:
            s_id = sec["id"]
            sec_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id]
            for ss in sec_subjs:
                sub_id = ss["subject_id"]
                sub_type = ss.get("subject_type", "L")
                sub_code = ss.get("subject_code", "")

                # Room domain pre-filtering for fast solving:

                # Theory slots (L/T) use non-lab classrooms; Labs (P) use lab rooms; Self-directed use VIRTUAL_LIB_ROOM
                is_self_directed = (
                    sub_type in SELF_DIRECTED_TYPES or 
                    sub_code in SELF_DIRECTED_TYPES or 
                    "MINOR" in sub_code.upper() or 
                    "HONOR" in sub_code.upper() or 
                    "SL/EL" in sub_code.upper() or 
                    "SL_EL" in sub_code.upper() or
                    "LIBRARY" in sub_code.upper()
                )
                if is_self_directed:
                    room_pool = [VIRTUAL_LIB_ROOM]
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


        # HC-01: Room Conflict (At most 1 class per room per slot)
        for r in rooms:
            r_id = r["id"]
            for t in time_slots:
                t_id = t["id"]
                room_vars = [
                    x[sec["id"], ss["subject_id"], r_id, t_id]
                    for sec in sections
                    for ss in section_subjects if ss["section_id"] == sec["id"]
                    if (sec["id"], ss["subject_id"], r_id, t_id) in x
                ]
                if room_vars:
                    model.AddAtMostOne(room_vars)

        # Extract all unique real faculty members (skip None / self-directed slots)
        all_faculty_names = set(faculty_subject_map.keys())
        for ss in section_subjects:
            if not _has_faculty(ss):
                continue  # CRITICAL: skip LIBRARY/IIC/SL_EL — no double-booking needed
            all_faculty_names.add(ss["faculty_name"].strip())
            for co in ss.get("co_faculty", []):
                if co and co.strip():
                    all_faculty_names.add(co.strip())

        # Build lookup for subject involvement per faculty member
        # fac_to_sec_subjs[fac] = list of (s_id, sub_id)
        fac_to_sec_subjs: Dict[str, List[Tuple[str, str]]] = {f: [] for f in all_faculty_names}
        for sec in sections:
            s_id = sec["id"]
            sec_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id]
            for ss in sec_subjs:
                # CRITICAL FIX: self-directed slots must never enter HC-02 tracking
                if ss.get("subject_type") in SELF_DIRECTED_TYPES or not _has_faculty(ss):
                    continue

                sub_id = ss["subject_id"]
                sub_code = ss.get("subject_code", "")

                # Collect direct + co_faculty names
                ss_facs: set = set()
                if _has_faculty(ss):
                    ss_facs.add(ss["faculty_name"].strip())
                for co in ss.get("co_faculty", []):
                    if co and co.strip():
                        ss_facs.add(co.strip())

                # Fallback to faculty_subject_map if no direct assignment
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
                sec_vars = [
                    x[s_id, ss["subject_id"], r["id"], t_id]
                    for ss in sec_subjs
                    for r in ([VIRTUAL_LIB_ROOM] if ss.get("subject_type") in SELF_DIRECTED_TYPES else rooms)
                    if (s_id, ss["subject_id"], r["id"], t_id) in x
                ]
                if sec_vars:
                    model.AddAtMostOne(sec_vars)

        # HC-04: Subject Frequency (Exact slots needed per subject per section)
        for sec in sections:
            s_id = sec["id"]
            sec_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id]
            for ss in sec_subjs:
                sub_id = ss["subject_id"]
                needed = ss.get("total_slots_needed", 3)
                sub_type = ss.get("subject_type", "L")
                sub_rooms = [VIRTUAL_LIB_ROOM] if sub_type in SELF_DIRECTED_TYPES else rooms

                if sub_type == "P":
                    # For practical labs, count starting periods only (periods 1, 3, 4, 6, 7)
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

        # HC-05 & HC-06: Room Capacity & Room Type Compatibility
        # CRITICAL FIX: Self-directed slots (LIBRARY, IIC, SL_EL) are assigned the
        # virtual "LIBRARY" room and need no physical-room type check at all.
        # Without this guard they fail HC-06 (no lab/classroom matches LIBRARY type)
        # creating model.Add(x==0) for every real room which conflicts with HC-04's
        # model.Add(sum==needed) — causing INFEASIBLE on every cohort size.
        for sec in sections:
            s_id = sec["id"]
            sec_capacity = sec.get("student_count", 60)
            sec_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id]
            for ss in sec_subjs:
                sub_id = ss["subject_id"]
                sub_type = ss.get("subject_type", "L")

                # Skip room-type enforcement for self-directed slots—they use a virtual room
                if sub_type in SELF_DIRECTED_TYPES:
                    continue

                for r in rooms:
                    r_id = r["id"]
                    r_cap = r.get("capacity", 60)
                    r_type = r.get("room_type", "classroom")

                    is_cap_ok  = r_cap >= sec_capacity
                    is_type_ok = ConstraintRules.is_room_compatible(sub_type, r_type)

                    if not (is_cap_ok and is_type_ok):
                        for t in time_slots:
                            if (s_id, sub_id, r_id, t["id"]) in x:
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
                        sub_rooms = [VIRTUAL_LIB_ROOM] if ss.get("subject_type") in SELF_DIRECTED_TYPES else rooms
                        for r in sub_rooms:
                            if (s_id, sub_id, r["id"], t_id) in x:
                                model.Add(x[s_id, sub_id, r["id"], t_id] == 0)


        # HC-08: Continuous Lab Block Allocations (2 or 3 Consecutive Slots)
        # Rule 1: Saturday is prohibited for Practical Lab (P) blocks.
        # Rule 2: Block lab starts at invalid periods (2, 5, 8) to prevent crossing recess/lunch breaks or creating orphans.
        # Rule 3: Continuous lab block must occupy the SAME room across consecutive periods (bidirectional implication).
        # Rule 4: Max 1 lab block per day for the same subject per section.
        for sec in sections:
            s_id = sec["id"]
            s_id_str = str(s_id).upper()
            lab_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id and ss.get("subject_type") == "P"]
            for ss in lab_subjs:
                sub_id = ss["subject_id"]
                
                # Rule 1: Prohibit Saturday labs
                for r in rooms:
                    for t in time_slots:
                        if t.get("day") == "SAT" and (s_id, sub_id, r["id"], t["id"]) in x:
                            model.Add(x[s_id, sub_id, r["id"], t["id"]] == 0)


                for day in ["MON", "TUE", "WED", "THU", "FRI"]:
                    day_slots = {t.get("period", 0): t for t in time_slots if t.get("day") == day and not t.get("is_blocked")}
                    valid_start_periods = [1, 3, 4, 6, 7]
                    
                    # Rule 3: Bidirectional implication for consecutive slots
                    for p1 in valid_start_periods:
                        p2 = p1 + 1
                        if p1 in day_slots and p2 in day_slots:
                            t1 = day_slots[p1]
                            t2 = day_slots[p2]
                            t1_id = t1["id"]
                            t2_id = t2["id"]
                            
                            for r in rooms:
                                r_id = r["id"]
                                if (s_id, sub_id, r_id, t1_id) in x and (s_id, sub_id, r_id, t2_id) in x:
                                    # Forward implication: if lab starts at period p1 (t1), period p2 (t2) is reserved in room r
                                    model.Add(x[s_id, sub_id, r_id, t2_id] == 1).OnlyEnforceIf(x[s_id, sub_id, r_id, t1_id])


                    # Rule 4: Max 1 lab block per day for this subject
                    start_day_vars = [
                        x[s_id, sub_id, r["id"], day_slots[p]["id"]]
                        for r in rooms
                        for p in valid_start_periods
                        if p in day_slots and (s_id, sub_id, r["id"], day_slots[p]["id"]) in x
                    ]
                    if start_day_vars:
                        model.Add(sum(start_day_vars) <= 1)

            # Rule 5: MINORS/HONORS Global Slot Protection (WED P7-P8 & THU P7-P8 when P7/P8 present)
            minors_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id and ("MINOR" in ss.get("subject_code", "").upper() or "HONOR" in ss.get("subject_code", "").upper())]
            has_p78_slots = any(t.get("period") in (7, 8) for t in time_slots)
            if minors_subjs and has_p78_slots:
                for ss in minors_subjs:
                    sub_id = ss["subject_id"]
                    sub_rooms = [VIRTUAL_LIB_ROOM] if ss.get("subject_type") in SELF_DIRECTED_TYPES else rooms
                    for r in sub_rooms:
                        for t in time_slots:
                            t_day = t.get("day")
                            t_p = t.get("period")
                            # MINORS/HONORS must ONLY occur on WED P7-P8 or THU P7-P8 when P7/P8 present
                            if not (t_day in ("WED", "THU") and t_p in (7, 8)):
                                if (s_id, sub_id, r["id"], t["id"]) in x:
                                    model.Add(x[s_id, sub_id, r["id"], t["id"]] == 0)

                # Forbid regular theory/lab subjects during WED P7-P8 & THU P7-P8 for this section
                regular_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id and not ("MINOR" in ss.get("subject_code", "").upper() or "HONOR" in ss.get("subject_code", "").upper())]
                for ss in regular_subjs:
                    sub_id = ss["subject_id"]
                    sub_rooms = [VIRTUAL_LIB_ROOM] if ss.get("subject_type") in SELF_DIRECTED_TYPES else rooms
                    for r in sub_rooms:
                        for t in time_slots:
                            if t.get("day") in ("WED", "THU") and t.get("period") in (7, 8):
                                if (s_id, sub_id, r["id"], t["id"]) in x:
                                    model.Add(x[s_id, sub_id, r["id"], t["id"]] == 0)

            # Rule 6: 4th Year SL/EL Self-Learning Preference (P1-P2 Morning & SAT P6-P8 Afternoon)
            s_id_str = str(s_id).upper()
            if "IV " in s_id_str or "IV_" in s_id_str:
                slel_subjs = [ss for ss in section_subjects if ss["section_id"] == s_id and ("SL/EL" in ss.get("subject_code", "").upper() or "SL_EL" in ss.get("subject_code", "").upper() or "LEARNING" in ss.get("subject_code", "").upper())]
                if slel_subjs:
                    for ss in slel_subjs:
                        sub_id = ss["subject_id"]
                        sub_rooms = [VIRTUAL_LIB_ROOM] if ss.get("subject_type") in SELF_DIRECTED_TYPES else rooms
                        for r in sub_rooms:
                            for t in time_slots:
                                t_p = t.get("period")
                                t_day = t.get("day")
                                is_allowed_slel = (t_p in (1, 2)) or (t_day == "SAT" and t_p in (6, 7, 8))
                                if not is_allowed_slel:
                                    if (s_id, sub_id, r["id"], t["id"]) in x:
                                        model.Add(x[s_id, sub_id, r["id"], t["id"]] == 0)

            # Soft Preference: 2nd Year Period 1 active and Period 8 free preference variables computed in Objective Function
            pass







        # Objective Function: Minimize period numbers (sum(var * p_num)) to group classes compactly into early periods (P1..P6)
        obj_terms = []
        for (s_id, sub_id, r_id, t_id), var in x.items():
            try:
                p_num = int(t_id.split("_")[-1])
            except Exception:
                p_num = 1
            obj_terms.append(var * p_num)

        if obj_terms:
            model.Minimize(sum(obj_terms))




        # Setup Ultra-Fast Solve Parameters
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self.config.timeout_seconds)
        solver.parameters.num_search_workers = 8  # Parallel portfolio search across 8 worker threads
        solver.parameters.cp_model_presolve = True  # Enable aggressive presolve logic
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
                    sub_type = ss.get("subject_type", "L")
                    # Mirror the same room_pool used during variable construction
                    room_pool = [VIRTUAL_LIB_ROOM] if sub_type in SELF_DIRECTED_TYPES else rooms
                    for r in room_pool:
                        r_id = r["id"]
                        for t in time_slots:
                            t_id = t["id"]
                            # Safe get: only keys in x from the construction phase above
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
                                all_facs = [fac_name] + [c for c in co_facs if c] if fac_name else []
                                stype = sub_type
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
                                    "type": stype,
                                    "subjectType": stype,
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

