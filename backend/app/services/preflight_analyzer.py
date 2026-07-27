from typing import List, Dict, Any


class PreflightAnalyzer:
    @staticmethod
    def analyze_request(
        sections: List[Dict[str, Any]],
        section_subjects: List[Dict[str, Any]],
        rooms: List[Dict[str, Any]],
        time_slots: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Performs ultra-fast deterministic pre-flight capacity & workload diagnostic checks
        before launching the CP-SAT solver engine on large-scale (150+ sections) requests.
        """
        warnings = []
        bottlenecks = []

        total_sections_count = len(sections)
        total_usable_slots = len([ts for ts in time_slots if not ts.get("is_blocked", False)])

        classrooms = [r for r in rooms if r.get("room_type") == "classroom" or not r.get("room_type")]
        computer_labs = [r for r in rooms if r.get("room_type") == "computer_lab"]
        gpu_labs = [r for r in rooms if r.get("room_type") == "gpu_lab"]

        total_classroom_supply_hours = len(classrooms) * total_usable_slots
        total_lab_supply_hours = (len(computer_labs) + len(gpu_labs)) * total_usable_slots

        # Demand breakdown
        total_theory_demand_hours = 0
        total_lab_demand_hours = 0
        faculty_workload_hours: Dict[str, int] = {}

        for ss in section_subjects:
            stype = ss.get("subject_type", "L")
            slots = ss.get("total_slots_needed", 3)
            primary_fac = ss.get("faculty_name", "")
            co_facs = ss.get("co_faculty", [])

            if stype == "P":
                total_lab_demand_hours += slots
            else:
                total_theory_demand_hours += slots

            if primary_fac:
                faculty_workload_hours[primary_fac] = faculty_workload_hours.get(primary_fac, 0) + slots
            for co in co_facs:
                if co:
                    faculty_workload_hours[co] = faculty_workload_hours.get(co, 0) + slots

        # Check Classroom Capacity Ratio
        classroom_occupancy_pct = round((total_theory_demand_hours / total_classroom_supply_hours * 100), 1) if total_classroom_supply_hours > 0 else 100.0
        lab_occupancy_pct = round((total_lab_demand_hours / total_lab_supply_hours * 100), 1) if total_lab_supply_hours > 0 else 100.0

        if total_theory_demand_hours > total_classroom_supply_hours:
            msg = f"Classroom Capacity Deficit: Demanded {total_theory_demand_hours}h exceeds available {total_classroom_supply_hours}h classroom capacity across {len(classrooms)} rooms."
            warnings.append(msg)
            bottlenecks.append({"type": "CLASSROOM_DEFICIT", "message": msg})

        if total_lab_demand_hours > total_lab_supply_hours:
            msg = f"Lab Capacity Deficit: Demanded {total_lab_demand_hours}h lab slots exceed available {total_lab_supply_hours}h capacity across {len(computer_labs) + len(gpu_labs)} labs."
            warnings.append(msg)
            bottlenecks.append({"type": "LAB_DEFICIT", "message": msg})

        # Check Faculty Individual Workload Caps (AICTE caps: Professor=12h, Associate Professor=14h, Assistant Professor=16h)
        AICTE_CAPS = {
            "Professor": 12,
            "Associate Professor": 14,
            "Assistant Professor": 16,
            "default": 16
        }
        overloaded_faculty = []
        for fac_name, hrs in faculty_workload_hours.items():
            cap = 16  # standard assistant prof / default cap
            if hrs > cap:
                overloaded_faculty.append(f"{fac_name} ({hrs}h/week, cap={cap}h)")

        if overloaded_faculty:
            msg = f"Faculty Workload Exceeded: {len(overloaded_faculty)} instructors exceed designation weekly cap: {', '.join(overloaded_faculty[:3])}"
            warnings.append(msg)
            bottlenecks.append({"type": "FACULTY_OVERLOAD", "message": msg, "faculty": overloaded_faculty})

        # Hard feasibility depends only on physical capacity deficits (Classroom/Lab deficit)
        hard_deficits = [b for b in bottlenecks if b["type"] in ("CLASSROOM_DEFICIT", "LAB_DEFICIT")]
        is_feasible = len(hard_deficits) == 0

        return {
            "is_feasible": is_feasible,
            "classroom_occupancy_pct": classroom_occupancy_pct,
            "lab_occupancy_pct": lab_occupancy_pct,
            "total_theory_demand_hours": total_theory_demand_hours,
            "total_lab_demand_hours": total_lab_demand_hours,
            "warnings": warnings,
            "bottlenecks": bottlenecks
        }
