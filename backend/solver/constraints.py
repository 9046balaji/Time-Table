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



