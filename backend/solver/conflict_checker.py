from dataclasses import dataclass, field
from typing import List, Dict, Any, Set, Tuple, Optional


@dataclass
class ClashDetail:
    clash_type: str  # "ROOM" | "FACULTY" | "STUDENT" | "BREAK"
    day: str
    period: int
    key: str  # room code or faculty name
    section_a: str
    subject_a: str
    section_b: str
    subject_b: str
    message: str


@dataclass
class ClashReport:
    room_clashes: int = 0
    physical_room_clashes: int = 0
    joint_section_slots: int = 0
    faculty_clashes: int = 0
    student_clashes: int = 0
    break_clashes: int = 0
    total_hard_violations: int = 0
    details: List[ClashDetail] = field(default_factory=list)


class ConflictChecker:
    IGNORED_ROOM_CODES = {
        "", "NONE", "LIBRARY", "BREAK", "LUNCH", "SL/EL", "MINORS/HONORS",
        "MINOR/HONOR", "MINORS", "HONORS", "N/A", "NA", "-", "ONLINE"
    }

    def detect(self, parsed_result: Any) -> ClashReport:
        report = ClashReport()
        slots = getattr(parsed_result, "raw_entries", parsed_result)

        # 1. Detect Room Clashes (HC-01)
        room_map: Dict[Tuple[str, int, str], List[Any]] = {}

        for slot in slots:
            room = (slot.room or "").strip().upper()
            if not room or room in self.IGNORED_ROOM_CODES:
                continue

            if slot.period is None or slot.period <= 0:
                continue

            # Ignore synchronized Minors/Honors global elective slots
            stype = getattr(slot, "subject_type", "")
            scode = (getattr(slot, "subject_code", "") or "").upper()
            if stype in ("MINORHONOR", "M_H") or "MINOR" in scode or "HONOR" in scode:
                continue

            key = (slot.day.upper(), slot.period, room)
            if key not in room_map:
                room_map[key] = []
            room_map[key].append(slot)

        for (day, period, room), occupied_slots in room_map.items():
            if len(occupied_slots) > 1:
                sections_seen = set()
                conflicting_slots = []
                for s in occupied_slots:
                    if s.section not in sections_seen:
                        sections_seen.add(s.section)
                        conflicting_slots.append(s)

                if len(conflicting_slots) > 1:
                    for i in range(len(conflicting_slots)):
                        for j in range(i + 1, len(conflicting_slots)):
                            sa, sb = conflicting_slots[i], conflicting_slots[j]
                            report.room_clashes += 1

                            # Distinguish physical room clashes (different subjects) vs joint section slots (same subject)
                            sub_a_norm = (sa.subject_code or "").upper().replace("(P)", "").replace("(T)", "").replace("(L)", "").strip()
                            sub_b_norm = (sb.subject_code or "").upper().replace("(P)", "").replace("(T)", "").replace("(L)", "").strip()
                            
                            is_physical_clash = (sub_a_norm != sub_b_norm)
                            if is_physical_clash:
                                report.physical_room_clashes += 1
                            else:
                                report.joint_section_slots += 1

                            clash_label = "ROOM_CLASH" if is_physical_clash else "JOINT_SECTION"
                            report.details.append(
                                ClashDetail(
                                    clash_type="ROOM",
                                    day=day,
                                    period=period,
                                    key=room,
                                    section_a=sa.section,
                                    subject_a=sa.subject_code,
                                    section_b=sb.section,
                                    subject_b=sb.subject_code,
                                    message=f"[{clash_label}] {day} Period-{period}, Room {room} → {sa.section}: {sa.subject_code} AND {sb.section}: {sb.subject_code}",
                                )
                            )

        # 2. Detect Faculty Clashes (HC-02)
        faculty_map: Dict[Tuple[str, int, str], List[Any]] = {}
        for slot in slots:
            faculty_list = getattr(slot, "faculty_list", [])
            if not faculty_list:
                continue
            if slot.period is None or slot.period <= 0:
                continue

            for fac in faculty_list:
                fac_clean = fac.strip()
                if not fac_clean:
                    continue
                key = (slot.day.upper(), slot.period, fac_clean)
                if key not in faculty_map:
                    faculty_map[key] = []
                faculty_map[key].append(slot)

        for (day, period, fac), occupied_slots in faculty_map.items():
            if len(occupied_slots) > 1:
                sections_seen = set()
                conflicting_slots = []
                for s in occupied_slots:
                    if s.section not in sections_seen:
                        sections_seen.add(s.section)
                        conflicting_slots.append(s)

                if len(conflicting_slots) > 1:
                    for i in range(len(conflicting_slots)):
                        for j in range(i + 1, len(conflicting_slots)):
                            sa, sb = conflicting_slots[i], conflicting_slots[j]
                            report.faculty_clashes += 1
                            report.details.append(
                                ClashDetail(
                                    clash_type="FACULTY",
                                    day=day,
                                    period=period,
                                    key=fac,
                                    section_a=sa.section,
                                    subject_a=sa.subject_code,
                                    section_b=sb.section,
                                    subject_b=sb.subject_code,
                                    message=f"{day} Period-{period}, Faculty {fac} → {sa.section}: {sa.subject_code} AND {sb.section}: {sb.subject_code}",
                                )
                            )

        report.total_hard_violations = report.room_clashes + report.faculty_clashes + report.student_clashes + report.break_clashes
        return report


class IncrementalValidator:
    """
    O(1) Hash-Map index validator for real-time drag-and-drop schedule editing.
    Allows testing whether moving a slot creates room or faculty conflicts instantaneously.
    """

    def __init__(self, entries: List[Any]):
        self.room_index: Dict[Tuple[str, int, str], Any] = {}
        self.faculty_index: Dict[Tuple[str, int, str], Any] = {}
        self.reindex(entries)

    def reindex(self, entries: List[Any]):
        self.room_index.clear()
        self.faculty_index.clear()
        for e in entries:
            day = getattr(e, "day", "MON")
            period = getattr(e, "period", 1)
            room = getattr(e, "room", "")
            faculty = getattr(e, "faculty", [])

            if room and room not in ConflictChecker.IGNORED_ROOM_CODES:
                self.room_index[(day, period, room.upper())] = e

            fac_list = [faculty] if isinstance(faculty, str) else faculty
            for fac in fac_list:
                if fac:
                    self.faculty_index[(day, period, fac.strip())] = e

    def validate_move(
        self,
        entry_id: Any,
        target_day: str,
        target_period: int,
        target_room: str,
        faculty_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        O(1) lookup to verify if target cell has any room or faculty collisions.
        """
        room_key = (target_day.upper(), target_period, target_room.upper())
        if room_key in self.room_index:
            existing = self.room_index[room_key]
            if getattr(existing, "id", None) != entry_id:
                return False, f"Room {target_room} is occupied by {getattr(existing, 'section', 'another section')} ({getattr(existing, 'subject', 'Subject')})"

        if faculty_name:
            fac_key = (target_day.upper(), target_period, faculty_name.strip())
            if fac_key in self.faculty_index:
                existing = self.faculty_index[fac_key]
                if getattr(existing, "id", None) != entry_id:
                    return False, f"Faculty {faculty_name} is already teaching {getattr(existing, 'section', 'another section')} at {target_day} P{target_period}"

        return True, None
