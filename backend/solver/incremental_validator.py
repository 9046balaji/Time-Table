from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Set
from backend.solver.constraints import ConstraintRules


@dataclass
class DragDropSwapRequest:
    entry_id: Any
    source_day: str
    source_period: int
    target_day: str
    target_period: int
    target_room_code: Optional[str] = None
    section_name: Optional[str] = None
    faculty_names: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    is_valid: bool
    clash_type: Optional[str] = None
    conflict_message: Optional[str] = None


class ScheduleIndexStore:
    """
    In-Memory inverted hash index mapping (day, period, room/fac/sec) -> entry.
    Enables O(1) cell swap validation in < 5ms without triggering full CP-SAT re-solves.
    """

    IGNORED_ROOM_CODES: Set[str] = ConstraintRules.IGNORED_ROOM_CODES

    def __init__(self, entries: Optional[List[Any]] = None):
        self._busy_index: Dict[Tuple[str, str, str, int], Dict[str, Any]] = {}
        self.room_occupancy: Dict[Tuple[str, int, str], Any] = {}
        self.faculty_schedule: Dict[Tuple[str, int, str], Any] = {}
        self.section_schedule: Dict[Tuple[str, int, str], Any] = {}
        if entries:
            self.index_timetable(entries)

    def index_timetable(self, entries: List[Any]) -> None:
        """Builds or refreshes the O(1) busy index from a timetable entry list."""
        self._busy_index.clear()
        self.room_occupancy.clear()
        self.faculty_schedule.clear()
        self.section_schedule.clear()

        for e in entries:
            if isinstance(e, dict):
                sec = str(e.get("section") or e.get("section_name") or e.get("sectionName") or "").strip()
                room = str(e.get("room") or e.get("room_code") or e.get("roomCode") or "").strip()
                day = ConstraintRules.normalize_string(e.get("day"))
                period = int(e.get("period") or 1)
                entry_id = e.get("id")
                subject = e.get("subject") or e.get("subject_code") or e.get("subjectCode")
                fac_list = e.get("faculty") or e.get("faculty_names") or e.get("facultyNames") or []
            else:
                sec = str(getattr(e, "section", "") or "").strip()
                room = str(getattr(e, "room", "") or "").strip()
                day = ConstraintRules.normalize_string(getattr(e, "day", ""))
                period = int(getattr(e, "period", 1) or 1)
                entry_id = getattr(e, "id", None)
                subject = getattr(e, "subject", "") or getattr(e, "subject_code", "")
                fac_list = getattr(e, "faculty", []) or getattr(e, "faculty_list", [])

            if isinstance(fac_list, str):
                fac_list = [f.strip() for f in fac_list.split(",") if f.strip()]

            if room and room.upper() not in self.IGNORED_ROOM_CODES:
                room_norm = room.upper()
                self.room_occupancy[(day, period, room_norm)] = e
                self._busy_index[("ROOM", room_norm, day, period)] = {
                    "id": entry_id, "section": sec, "subject": subject
                }

            if sec:
                sec_norm = sec.upper()
                self.section_schedule[(day, period, sec_norm)] = e
                self._busy_index[("SECTION", sec_norm, day, period)] = {
                    "id": entry_id, "subject": subject, "room": room
                }

            for f in fac_list:
                f_str = str(f).strip()
                if f_str and f_str.upper() not in ("", "UNDEFINED", "NULL", "NONE"):
                    f_norm = f_str.upper()
                    self.faculty_schedule[(day, period, f_norm)] = e
                    self._busy_index[("FACULTY", f_norm, day, period)] = {
                        "id": entry_id, "section": sec, "room": room, "subject": subject
                    }

    def validate_move(
        self,
        entry_id: Any,
        section_name: Optional[str],
        faculty_names: List[str],
        target_day: str,
        target_period: int,
        target_room_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates a manual drag-and-drop cell swap in < 5ms.
        """
        t_day = ConstraintRules.normalize_string(target_day)
        t_period = int(target_period)
        t_room = target_room_code.strip().upper() if target_room_code else None

        # 1. Room Clash Check
        if t_room and t_room not in self.IGNORED_ROOM_CODES:
            r_busy = self._busy_index.get(("ROOM", t_room, t_day, t_period))
            if r_busy and str(r_busy["id"]) != str(entry_id):
                return {
                    "is_valid": False,
                    "clash_type": "ROOM",
                    "conflict_message": f"Room {target_room_code or t_room} is already booked by Section {r_busy.get('section')} ({r_busy.get('subject')}) on {t_day} Period {t_period}."
                }

        # 2. Faculty Clash Check
        for fac in faculty_names:
            f_norm = fac.strip().upper()
            if f_norm and f_norm not in ("", "UNDEFINED", "NULL", "NONE"):
                f_busy = self._busy_index.get(("FACULTY", f_norm, t_day, t_period))
                if f_busy and str(f_busy["id"]) != str(entry_id):
                    return {
                        "is_valid": False,
                        "clash_type": "FACULTY",
                        "conflict_message": f"Faculty {fac} is already teaching Section {f_busy.get('section')} in Room {f_busy.get('room')} on {t_day} Period {t_period}."
                    }

        # 3. Section Clash Check
        sec_norm = section_name.strip().upper() if section_name else ""
        if sec_norm:
            s_busy = self._busy_index.get(("SECTION", sec_norm, t_day, t_period))
            if s_busy and str(s_busy["id"]) != str(entry_id):
                return {
                    "is_valid": False,
                    "clash_type": "SECTION",
                    "conflict_message": f"Section {section_name} already has class {s_busy.get('subject')} scheduled on {t_day} Period {t_period}."
                }

        return {
            "is_valid": True,
            "clash_type": None,
            "conflict_message": None
        }


class IncrementalValidator:
    """
    High-level validator wrapping ScheduleIndexStore for drag-and-drop user actions.
    """

    def __init__(self, index_store: ScheduleIndexStore):
        self.store = index_store

    def validate_swap(self, req: DragDropSwapRequest) -> ValidationResult:
        res = self.store.validate_move(
            entry_id=req.entry_id,
            section_name=req.section_name or "",
            faculty_names=req.faculty_names or [],
            target_day=req.target_day,
            target_period=req.target_period,
            target_room_code=req.target_room_code
        )
        return ValidationResult(
            is_valid=res["is_valid"],
            clash_type=res["clash_type"],
            conflict_message=res["conflict_message"]
        )

