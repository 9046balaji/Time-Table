from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple, Optional


@dataclass
class DragDropSwapRequest:
    entry_id: int
    source_day: str
    source_period: int
    target_day: str
    target_period: int
    target_room_code: Optional[str] = None
    faculty_names: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    is_valid: bool
    clash_type: Optional[str] = None  # "ROOM" | "FACULTY" | "CAPACITY"
    conflict_message: Optional[str] = None


class ScheduleIndexStore:
    """
    In-memory $O(1)$ Hash Index Store for real-time drag-and-drop cell validation.
    Stores index mappings for room occupancy and faculty scheduling.
    """

    def __init__(self, entries: Optional[List[Any]] = None):
        self.room_occupancy: Dict[Tuple[str, int, str], Any] = {}
        self.faculty_schedule: Dict[Tuple[str, int, str], Any] = {}
        if entries:
            self.build_index(entries)

    def build_index(self, entries: List[Any]):
        self.room_occupancy.clear()
        self.faculty_schedule.clear()

        for e in entries:
            day = getattr(e, "day", "MON").upper()
            period = getattr(e, "period", 1)
            room = getattr(e, "room", getattr(e, "room_code", "")).upper()
            faculty = getattr(e, "faculty", getattr(e, "faculty_name", []))

            if room and room not in ("LIBRARY", "BREAK", "LUNCH", "NONE", "ONLINE"):
                self.room_occupancy[(day, period, room)] = e

            fac_list = [faculty] if isinstance(faculty, str) else (faculty or [])
            for fac in fac_list:
                if fac and str(fac).strip():
                    self.faculty_schedule[(day, period, str(fac).strip())] = e


class IncrementalValidator:
    """
    $O(1)$ Incremental validation engine testing slot moves without re-running CP-SAT.
    """

    def __init__(self, index_store: ScheduleIndexStore):
        self.index = index_store

    def validate_swap(self, req: DragDropSwapRequest) -> ValidationResult:
        target_day = req.target_day.upper()
        target_period = req.target_period
        target_room = (req.target_room_code or "").upper()

        # Check Room Conflict
        if target_room:
            room_key = (target_day, target_period, target_room)
            if room_key in self.index.room_occupancy:
                occupant = self.index.room_occupancy[room_key]
                if getattr(occupant, "id", None) != req.entry_id:
                    sec = getattr(occupant, "section", "Another section")
                    subj = getattr(occupant, "subject", "Subject")
                    return ValidationResult(
                        is_valid=False,
                        clash_type="ROOM",
                        conflict_message=f"Room {target_room} is already booked by {sec} ({subj}) at {target_day} P{target_period}."
                    )

        # Check Faculty Conflict
        for fac in req.faculty_names:
            fac_clean = str(fac).strip()
            if fac_clean:
                fac_key = (target_day, target_period, fac_clean)
                if fac_key in self.index.faculty_schedule:
                    occupant = self.index.faculty_schedule[fac_key]
                    if getattr(occupant, "id", None) != req.entry_id:
                        sec = getattr(occupant, "section", "Another section")
                        return ValidationResult(
                            is_valid=False,
                            clash_type="FACULTY",
                            conflict_message=f"Faculty {fac_clean} is already teaching {sec} at {target_day} P{target_period}."
                        )

        return ValidationResult(is_valid=True)
