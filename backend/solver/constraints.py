from typing import List, Dict, Any, Tuple, Set, Optional
from functools import lru_cache


class ConstraintRules:
    """
    Centralized validation rules and constraint helper logic for VFSTR Timetable Scheduler.
    Implements validation logic for Hard Constraints (HC-01 to HC-13) and Soft Constraints (SC-01 to SC-10).
    """

    LAB_ROOM_TYPES: Set[str] = {"computer_lab", "gpu_lab", "lab", "project_lab"}
    CLASSROOM_TYPES: Set[str] = {"classroom", "seminar_hall", "lecture_hall"}
    GPU_LAB_TYPES: Set[str] = {"gpu_lab"}

    # Special slots that cannot have normal subject classes
    BLOCKED_SLOT_TIMES: Set[str] = {
        "09:55-10:10", "12:40-13:40", "09:55-10:10 AM", "12:40-01:40 PM"
    }
    
    # Room codes to ignore during room clash detection (non-physical / global / virtual slots)
    IGNORED_ROOM_CODES: Set[str] = {
        "", "NONE", "LIBRARY", "BREAK", "LUNCH", "SL/EL", "MINORS/HONORS",
        "MINOR/HONOR", "MINORS", "HONORS", "N/A", "NA", "-", "ONLINE"
    }

    # Faculty workload limits (hours per week) based on rank
    FACULTY_RANK_MAX_HOURS: Dict[str, int] = {
        "Professor": 12,
        "Associate Professor": 14,
        "Assistant Professor": 16,
        "Default": 16,
    }

    BREAK_GUARD_PAIRS: Set[Tuple[int, int]] = {(2, 3), (5, 6)}
    VALID_LAB_START_PERIODS: Set[int] = {1, 3, 4, 6, 7}

    @staticmethod
    @lru_cache(maxsize=2048)
    def normalize_string(val: Optional[str]) -> str:
        """Fast memoized string normalization for high-frequency constraint checks."""
        if not val:
            return ""
        return val.strip().upper()

    @classmethod
    def is_lab_subject(cls, subject_code: Optional[str], subject_type: str = "L") -> bool:
        """HC-06 / HC-08: Determine if a subject requires lab infrastructure or consecutive allocation."""
        if not subject_code:
            return subject_type.upper() in ("P", "LAB", "PRACTICAL")
        
        if subject_type.upper() in ("P", "LAB", "PRACTICAL"):
            return True

        code_upper = cls.normalize_string(subject_code)
        return (
            "(P)" in code_upper
            or "LAB" in code_upper
            or "(P&T)" in code_upper
            or "(T&P)" in code_upper
        )

    @classmethod
    def is_tutorial_subject(cls, subject_code: Optional[str], subject_type: str = "L") -> bool:
        """Check if subject is a tutorial session."""
        if subject_type.upper() == "T":
            return True
        code_upper = cls.normalize_string(subject_code)
        return "(T)" in code_upper

    @classmethod
    def is_room_compatible(cls, subject_type: str, room_type: str) -> bool:
        """HC-06: Room Type Match validation."""
        r_type = room_type.lower().strip()
        s_type = subject_type.upper().strip()
        if s_type in ("P", "LAB", "PRACTICAL"):
            return r_type in cls.LAB_ROOM_TYPES
        return True

    @classmethod
    def is_break_slot(cls, period: int, slot_label: str = "") -> bool:
        """HC-07: Break/Lunch Block Protection validation."""
        label_norm = cls.normalize_string(slot_label)
        if label_norm in ("BREAK", "LUNCH"):
            return True
        return False

    @classmethod
    def get_max_faculty_hours(cls, rank: Optional[str]) -> int:
        """HC-11: Faculty Workload Limit by Rank."""
        if not rank:
            return cls.FACULTY_RANK_MAX_HOURS["Default"]
        return cls.FACULTY_RANK_MAX_HOURS.get(rank.strip(), cls.FACULTY_RANK_MAX_HOURS["Default"])

    @classmethod
    def is_valid_lab_pair(cls, p1: int, p2: int, day: str = "MON") -> bool:
        """HC-08: Lab Consecutiveness & Break Guard validation."""
        day_norm = cls.normalize_string(day)
        if day_norm in ("SAT", "SATURDAY"):
            return False
        if (p1, p2) in cls.BREAK_GUARD_PAIRS:
            return False
        return p1 in cls.VALID_LAB_START_PERIODS and p2 == p1 + 1

    @staticmethod
    def check_faculty_daily_cap(daily_classes_count: int, max_cap: int = 5) -> bool:
        """HC-09: Faculty Daily Teaching Cap (max 5 classes/day per teacher)."""
        return daily_classes_count <= max_cap

    @staticmethod
    def check_continuous_teaching_limit(consecutive_periods_count: int, max_consecutive: int = 4) -> bool:
        """HC-10: Max Continuous Teaching Limit (max 4 consecutive periods)."""
        return consecutive_periods_count <= max_consecutive

    @classmethod
    def check_faculty_rank_workload_cap(cls, weekly_hours: int, rank: str = "Assistant Professor") -> bool:
        """HC-11: Faculty Rank Workload Cap Validation."""
        max_h = cls.get_max_faculty_hours(rank)
        return weekly_hours <= max_h

    @classmethod
    def check_minors_honors_slot_protection(cls, day: str, period: int, subject_code: Optional[str]) -> bool:
        """HC-12 / HC-09: Minors/Honors Global Slot Protection (Wednesday P7-P8 & Thursday P7-P8)."""
        day_norm = cls.normalize_string(day)
        is_minors_slot = (day_norm in ("WED", "WEDNESDAY", "THU", "THURSDAY")) and (period in (7, 8))
        
        code_norm = cls.normalize_string(subject_code)
        is_minors_code = ("MINOR" in code_norm or "HONOR" in code_norm)

        if is_minors_slot and not is_minors_code:
            return False
        if is_minors_code and not is_minors_slot:
            return False
        return True

    @classmethod
    def check_4th_year_slel_slot_protection(
        cls, day: str, period: int, subject_code: Optional[str], is_4th_year: bool = False
    ) -> bool:
        """HC-13 / HC-10: 4th Year SL/EL Fixed Block Protection (Periods 1 & 2 MON-SAT, or SAT P6-P8)."""
        if not is_4th_year:
            return True

        code_norm = cls.normalize_string(subject_code)
        is_slel_code = ("SL/EL" in code_norm or "SL_EL" in code_norm or "LEARNING" in code_norm)
        
        day_norm = cls.normalize_string(day)
        is_allowed_period = (period in (1, 2)) or (day_norm in ("SAT", "SATURDAY") and period in (6, 7, 8))
        if is_slel_code and not is_allowed_period:
            return False
        return True

    # Campus Building Block Partitioning (SC-09 Locality & Transit Minimization)
    U_BLOCK_ROOMS: Set[str] = {
        "601", "602", "603", "604", "605", "606", "607", "608", "609", "610",
        "611", "612", "613", "614", "615", "616", "617", "618", "619", "619A",
        "401", "402", "418", "501", "501A", "502", "514", "514-A", "514-B",
        "514A", "514B", "518", "AFTF-12", "AFTF-13", "AFTF-14", "AFF-09", "AFF-10", "AFF-9"
    }
    H_BLOCK_ROOMS: Set[str] = {"215", "216", "217", "218"}
    A_BLOCK_ROOMS: Set[str] = {"/AL/IL", "A-Block First Floor"}

    GPU_PRIORITY_SUBJECTS: Set[str] = {"DL", "CV", "MLOP", "GENAI"}

    @classmethod
    def get_room_block(cls, room_obj: Any) -> str:
        """Returns the campus building block for a given room code or room dict/model."""
        if not room_obj:
            return "UNKNOWN"
        
        if isinstance(room_obj, dict):
            blk = room_obj.get("block") or room_obj.get("building_block")
            if blk:
                return cls.normalize_string(str(blk))
            room_code = str(room_obj.get("code") or room_obj.get("id") or "")
        elif hasattr(room_obj, "block") and getattr(room_obj, "block"):
            return cls.normalize_string(str(getattr(room_obj, "block")))
        else:
            room_code = str(room_obj)

        r_norm = cls.normalize_string(room_code).replace(" ", "")
        if r_norm in cls.H_BLOCK_ROOMS or "21" in r_norm:
            return "H-BLOCK"
        if r_norm in cls.A_BLOCK_ROOMS or "A-BLOCK" in r_norm:
            return "A-BLOCK"
        if r_norm in cls.U_BLOCK_ROOMS or "AFTF" in r_norm or "AFF" in r_norm or (len(r_norm) >= 3 and r_norm[0] in "456"):
            return "U-BLOCK"
        return "EXTERNAL"

    @classmethod
    def calculate_block_transit_score(cls, slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audits SC-09: Inter-block student and faculty transit between adjacent periods."""
        slots_by_sec_day: Dict[Tuple[str, str], Dict[int, str]] = {}
        for s in slots:
            sec = str(s.get("section") or s.get("sectionName") or "")
            day = str(s.get("day") or "")
            period = int(s.get("period") or 1)
            room = str(s.get("room") or s.get("roomCode") or "")
            if sec and day and room and room not in cls.IGNORED_ROOM_CODES:
                slots_by_sec_day.setdefault((sec, day), {})[period] = room

        cross_block_sprints = 0
        total_transitions = 0
        details = []

        for (sec, day), period_rooms in slots_by_sec_day.items():
            sorted_periods = sorted(period_rooms.keys())
            for i in range(len(sorted_periods) - 1):
                p1 = sorted_periods[i]
                p2 = sorted_periods[i + 1]
                if p2 == p1 + 1:  # Consecutive periods
                    total_transitions += 1
                    b1 = cls.get_room_block(period_rooms[p1])
                    b2 = cls.get_room_block(period_rooms[p2])
                    if b1 != "UNKNOWN" and b2 != "UNKNOWN" and b1 != b2:
                        cross_block_sprints += 1
                        details.append({
                            "section": sec,
                            "day": day,
                            "from_period": p1,
                            "to_period": p2,
                            "from_room": period_rooms[p1],
                            "to_room": period_rooms[p2],
                            "from_block": b1,
                            "to_block": b2,
                        })

        transit_ratio = round((cross_block_sprints / max(total_transitions, 1)) * 100.0, 1)
        return {
            "total_consecutive_transitions": total_transitions,
            "cross_block_sprints": cross_block_sprints,
            "cross_block_pct": transit_ratio,
            "is_optimal": cross_block_sprints <= 5,
            "details": details[:10]
        }

    @classmethod
    def validate_section_weekly_quotas(cls, slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates academic section teaching quotas:
        - 2nd Year: exactly 36 teaching slots
        - 3rd Year: exactly 45 teaching slots
        - 4th Year: exactly 39 teaching slots
        """
        counts_by_sec: Dict[str, int] = {}
        for s in slots:
            sec = str(s.get("section") or s.get("sectionName") or "")
            stype = str(s.get("type") or s.get("entry_type") or "L").upper()
            code = cls.normalize_string(str(s.get("subject") or s.get("subjectCode") or ""))
            if code not in ("LIBRARY", "BREAK", "LUNCH") and stype not in ("BREAK", "LUNCH", "LIBRARY"):
                counts_by_sec[sec] = counts_by_sec.get(sec, 0) + 1

        deviations = {}
        for sec, count in counts_by_sec.items():
            expected = 36 if "II " in sec else (45 if "III " in sec else (39 if "IV " in sec else 36))
            if count != expected:
                deviations[sec] = {"actual": count, "expected": expected, "diff": count - expected}

        return {
            "total_sections_checked": len(counts_by_sec),
            "quota_compliant_count": len(counts_by_sec) - len(deviations),
            "deviation_count": len(deviations),
            "is_compliant": len(deviations) == 0,
            "deviations": deviations
        }

    @classmethod
    def validate_library_allocation(cls, slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates Library rules (SC-04):
        - 2nd Year: exactly 1 Library slot per week, ideally in P4 or P5.
        - 3rd & 4th Year: 0 Library slots.
        """
        lib_slots_by_sec: Dict[str, List[int]] = {}
        for s in slots:
            sec = str(s.get("section") or s.get("sectionName") or "")
            code = cls.normalize_string(str(s.get("subject") or s.get("subjectCode") or ""))
            stype = str(s.get("type") or s.get("entry_type") or "").upper()
            if "LIBRARY" in code or stype == "LIBRARY":
                lib_slots_by_sec.setdefault(sec, []).append(int(s.get("period") or 1))

        violations = []
        for sec, p_list in lib_slots_by_sec.items():
            if "III " in sec or "IV " in sec:
                violations.append(f"{sec} has {len(p_list)} Library slot(s) (Expected: 0 for 3rd/4th Year)")
            elif "II " in sec:
                if len(p_list) != 1:
                    violations.append(f"{sec} has {len(p_list)} Library slot(s) (Expected: 1 for 2nd Year)")
                elif p_list[0] not in (4, 5):
                    # Soft warning: preferably midday
                    pass

        return {
            "total_sections_with_library": len(lib_slots_by_sec),
            "violation_count": len(violations),
            "is_valid": len(violations) == 0,
            "violations": violations
        }



