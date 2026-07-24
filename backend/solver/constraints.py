from typing import List, Dict, Any, Tuple, Set


class ConstraintRules:
    LAB_ROOM_TYPES = {"computer_lab", "gpu_lab", "lab", "project_lab"}
    CLASSROOM_TYPES = {"classroom", "seminar_hall", "lecture_hall"}
    GPU_LAB_TYPES = {"gpu_lab"}

    # Special slots that cannot have normal subject classes
    BLOCKED_SLOT_TIMES = {"09:55-10:10", "12:40-13:40", "09:55-10:10 AM", "12:40-01:40 PM"}
    IGNORED_ROOM_CODES = {
        "", "NONE", "LIBRARY", "BREAK", "LUNCH", "SL/EL", "MINORS/HONORS",
        "MINOR/HONOR", "MINORS", "HONORS", "N/A", "NA", "-", "ONLINE"
    }

    # Faculty workload limits (hours per week) based on rank
    FACULTY_RANK_MAX_HOURS = {
        "Professor": 12,
        "Associate Professor": 14,
        "Assistant Professor": 16,
        "Default": 16,
    }

    @staticmethod
    def is_lab_subject(subject_code: str, subject_type: str = "L") -> bool:
        code_upper = subject_code.upper()
        if subject_type == "P" or "(P)" in code_upper or "LAB" in code_upper or "(P&T)" in code_upper or "(T&P)" in code_upper:
            return True
        return False

    @staticmethod
    def is_tutorial_subject(subject_code: str, subject_type: str = "L") -> bool:
        code_upper = subject_code.upper()
        return subject_type == "T" or "(T)" in code_upper

    @staticmethod
    def is_room_compatible(subject_type: str, room_type: str) -> bool:
        r_type = room_type.lower()
        if subject_type == "P":
            return r_type in ConstraintRules.LAB_ROOM_TYPES
        return True

    @staticmethod
    def is_break_slot(period: int, slot_label: str = "") -> bool:
        if slot_label.upper() in ["BREAK", "LUNCH"]:
            return True
        return False

    @staticmethod
    def get_max_faculty_hours(rank: str) -> int:
        return ConstraintRules.FACULTY_RANK_MAX_HOURS.get(rank, ConstraintRules.FACULTY_RANK_MAX_HOURS["Default"])

    # HC-09: Faculty Daily Teaching Cap (max 5 classes/day per teacher)
    @staticmethod
    def check_faculty_daily_cap(daily_classes_count: int, max_cap: int = 5) -> bool:
        return daily_classes_count <= max_cap

    # HC-10: Max Continuous Teaching Limit (max 4 consecutive periods)
    @staticmethod
    def check_continuous_teaching_limit(consecutive_periods_count: int, max_consecutive: int = 4) -> bool:
        return consecutive_periods_count <= max_consecutive
