from dataclasses import dataclass, field
from typing import List, Dict, Any, Set, Tuple, Optional
from backend.solver.constraints import ConstraintRules


@dataclass
class ClashDetail:
    clash_type: str  # "ROOM" | "FACULTY" | "STUDENT" | "BREAK"
    day: str
    period: int
    key: str  # room code, faculty name, or section name
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
    """
    High-performance conflict analysis engine.
    Analyzes timetable entries to detect HC-01 (Room), HC-02 (Faculty), HC-03 (Student/Section), and HC-07 (Break) conflicts.
    """

    IGNORED_ROOM_CODES: Set[str] = ConstraintRules.IGNORED_ROOM_CODES

    def detect(self, parsed_result: Any) -> ClashReport:
        """
        Runs comprehensive hard constraint conflict detection across all slots.
        Returns a detailed ClashReport with counts and individual clash records.
        """
        report = ClashReport()
        slots: List[Any] = getattr(parsed_result, "raw_entries", parsed_result)
        if not isinstance(slots, list):
            return report

        # Pre-indexed buckets for fast single-pass grouping
        room_map: Dict[Tuple[str, int, str], List[Any]] = {}
        faculty_map: Dict[Tuple[str, int, str], List[Any]] = {}
        section_map: Dict[Tuple[str, int, str], List[Any]] = {}

        for slot in slots:
            period = getattr(slot, "period", None)
            if period is None or period <= 0:
                continue

            day_norm = ConstraintRules.normalize_string(getattr(slot, "day", ""))
            if not day_norm:
                continue

            section = getattr(slot, "section", "") or ""
            subject_code = getattr(slot, "subject_code", "") or ""
            subject_type = getattr(slot, "subject_type", "") or ""
            code_norm = ConstraintRules.normalize_string(subject_code)

            # ---------------------------------------------------------
            # 0. Check Break / Lunch Conflicts (HC-07)
            # ---------------------------------------------------------
            slot_label = getattr(slot, "subject_type", "") or getattr(slot, "slot_label", "") or ""
            if ConstraintRules.is_break_slot(period, slot_label):
                report.break_clashes += 1
                report.details.append(
                    ClashDetail(
                        clash_type="BREAK",
                        day=day_norm,
                        period=period,
                        key="BREAK_SLOT",
                        section_a=section,
                        subject_a=subject_code,
                        section_b="N/A",
                        subject_b="N/A",
                        message=f"[BREAK_CLASH] {day_norm} Period-{period} → {section} scheduled during break/lunch",
                    )
                )


            # ---------------------------------------------------------
            # 1. Bucket Room Occupancy (HC-01)
            # ---------------------------------------------------------
            room = ConstraintRules.normalize_string(getattr(slot, "room", ""))
            is_minors = (
                subject_type in ("MINORHONOR", "M_H")
                or "MINOR" in code_norm
                or "HONOR" in code_norm
            )

            if room and room not in self.IGNORED_ROOM_CODES and not is_minors:
                room_key = (day_norm, period, room)
                if room_key not in room_map:
                    room_map[room_key] = []
                room_map[room_key].append(slot)

            # ---------------------------------------------------------
            # 2. Bucket Faculty Assignments (HC-02)
            # ---------------------------------------------------------
            faculty_list = getattr(slot, "faculty_list", [])
            if faculty_list:
                for fac in faculty_list:
                    fac_clean = fac.strip()
                    if fac_clean:
                        fac_key = (day_norm, period, fac_clean)
                        if fac_key not in faculty_map:
                            faculty_map[fac_key] = []
                        faculty_map[fac_key].append(slot)

            # ---------------------------------------------------------
            # 3. Bucket Student Section Assignments (HC-03)
            # ---------------------------------------------------------
            if section and not is_minors:
                sec_key = (day_norm, period, section)
                if sec_key not in section_map:
                    section_map[sec_key] = []
                section_map[sec_key].append(slot)

        # =============================================================
        # Process Room Clashes (HC-01)
        # =============================================================
        for (day, period, room), occupied_slots in room_map.items():
            if len(occupied_slots) <= 1:
                continue

            # Deduplicate by section to find distinct section collisions
            distinct_slots_by_section: Dict[str, Any] = {}
            for s in occupied_slots:
                sec = getattr(s, "section", "")
                if sec not in distinct_slots_by_section:
                    distinct_slots_by_section[sec] = s

            conflicting_slots = list(distinct_slots_by_section.values())
            if len(conflicting_slots) > 1:
                for i in range(len(conflicting_slots)):
                    for j in range(i + 1, len(conflicting_slots)):
                        sa, sb = conflicting_slots[i], conflicting_slots[j]
                        report.room_clashes += 1

                        sub_a_code = getattr(sa, "subject_code", "") or ""
                        sub_b_code = getattr(sb, "subject_code", "") or ""
                        sub_a_norm = ConstraintRules.normalize_string(sub_a_code).replace("(P)", "").replace("(T)", "").replace("(L)", "").strip()
                        sub_b_norm = ConstraintRules.normalize_string(sub_b_code).replace("(P)", "").replace("(T)", "").replace("(L)", "").strip()

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
                                section_a=getattr(sa, "section", ""),
                                subject_a=sub_a_code,
                                section_b=getattr(sb, "section", ""),
                                subject_b=sub_b_code,
                                message=f"[{clash_label}] {day} Period-{period}, Room {room} → {getattr(sa, 'section', '')}: {sub_a_code} AND {getattr(sb, 'section', '')}: {sub_b_code}",
                            )
                        )

        # =============================================================
        # Process Faculty Clashes (HC-02)
        # =============================================================
        for (day, period, fac), occupied_slots in faculty_map.items():
            if len(occupied_slots) <= 1:
                continue

            distinct_slots_by_section = {}
            for s in occupied_slots:
                sec = getattr(s, "section", "")
                if sec not in distinct_slots_by_section:
                    distinct_slots_by_section[sec] = s

            conflicting_slots = list(distinct_slots_by_section.values())
            if len(conflicting_slots) > 1:
                for i in range(len(conflicting_slots)):
                    for j in range(i + 1, len(conflicting_slots)):
                        sa, sb = conflicting_slots[i], conflicting_slots[j]
                        report.faculty_clashes += 1
                        sub_a_code = getattr(sa, "subject_code", "") or ""
                        sub_b_code = getattr(sb, "subject_code", "") or ""
                        report.details.append(
                            ClashDetail(
                                clash_type="FACULTY",
                                day=day,
                                period=period,
                                key=fac,
                                section_a=getattr(sa, "section", ""),
                                subject_a=sub_a_code,
                                section_b=getattr(sb, "section", ""),
                                subject_b=sub_b_code,
                                message=f"[FACULTY_CLASH] {day} Period-{period}, Faculty {fac} → {getattr(sa, 'section', '')}: {sub_a_code} AND {getattr(sb, 'section', '')}: {sub_b_code}",
                            )
                        )

        # =============================================================
        # Process Student Section Clashes (HC-03)
        # =============================================================
        for (day, period, sec), occupied_slots in section_map.items():
            if len(occupied_slots) <= 1:
                continue

            for i in range(len(occupied_slots)):
                for j in range(i + 1, len(occupied_slots)):
                    sa, sb = occupied_slots[i], occupied_slots[j]
                    sub_a_code = getattr(sa, "subject_code", "") or ""
                    sub_b_code = getattr(sb, "subject_code", "") or ""
                    room_a = getattr(sa, "room", "") or ""
                    room_b = getattr(sb, "room", "") or ""

                    # Double booked if in different rooms/subjects
                    if room_a != room_b or sub_a_code != sub_b_code:
                        report.student_clashes += 1
                        report.details.append(
                            ClashDetail(
                                clash_type="STUDENT",
                                day=day,
                                period=period,
                                key=sec,
                                section_a=sec,
                                subject_a=sub_a_code,
                                section_b=sec,
                                subject_b=sub_b_code,
                                message=f"[STUDENT_CLASH] {day} Period-{period}, Section {sec} double-booked in Room {room_a} ({sub_a_code}) AND Room {room_b} ({sub_b_code})",
                            )
                        )

        report.total_hard_violations = (
            report.room_clashes
            + report.faculty_clashes
            + report.student_clashes
            + report.break_clashes
        )
        return report


class IncrementalValidator:
    """
    O(1) Hash-Map index validator for real-time drag-and-drop schedule editing.
    Allows testing whether moving a slot creates room, faculty, or section conflicts instantaneously.
    """

    def __init__(self, entries: List[Any]):
        self.room_index: Dict[Tuple[str, int, str], Any] = {}
        self.faculty_index: Dict[Tuple[str, int, str], Any] = {}
        self.section_index: Dict[Tuple[str, int, str], Any] = {}
        self.reindex(entries)

    def reindex(self, entries: List[Any]) -> None:
        """Rebuilds O(1) hash indices for room, faculty, and section slots."""
        self.room_index.clear()
        self.faculty_index.clear()
        self.section_index.clear()

        for e in entries:
            day = ConstraintRules.normalize_string(getattr(e, "day", "MON"))
            period = getattr(e, "period", 1)
            if period is None or period <= 0:
                continue

            room = ConstraintRules.normalize_string(getattr(e, "room", ""))
            section = getattr(e, "section", "")

            if room and room not in ConflictChecker.IGNORED_ROOM_CODES:
                self.room_index[(day, period, room)] = e

            if section:
                self.section_index[(day, period, section)] = e

            faculty = getattr(e, "faculty", []) or getattr(e, "faculty_list", [])
            fac_list = [faculty] if isinstance(faculty, str) else faculty
            for fac in fac_list:
                if fac and isinstance(fac, str):
                    fac_clean = fac.strip()
                    if fac_clean:
                        self.faculty_index[(day, period, fac_clean)] = e

    def validate_move(
        self,
        entry_id: Any,
        target_day: str,
        target_period: int,
        target_room: str,
        faculty_name: Optional[str] = None,
        section_name: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        O(1) lookup to verify if target cell has any room, faculty, or section collisions.
        Returns (is_valid, error_message).
        """
        day_norm = ConstraintRules.normalize_string(target_day)
        room_norm = ConstraintRules.normalize_string(target_room)

        # 1. Room collision check
        if room_norm and room_norm not in ConflictChecker.IGNORED_ROOM_CODES:
            room_key = (day_norm, target_period, room_norm)
            if room_key in self.room_index:
                existing = self.room_index[room_key]
                if getattr(existing, "id", None) != entry_id:
                    sec = getattr(existing, "section", "another section")
                    sub = getattr(existing, "subject_code", getattr(existing, "subject", "Subject"))
                    return False, f"Room {target_room} is occupied by {sec} ({sub})"

        # 2. Faculty double-booking check
        if faculty_name:
            fac_clean = faculty_name.strip()
            if fac_clean:
                fac_key = (day_norm, target_period, fac_clean)
                if fac_key in self.faculty_index:
                    existing = self.faculty_index[fac_key]
                    if getattr(existing, "id", None) != entry_id:
                        sec = getattr(existing, "section", "another section")
                        return False, f"Faculty {faculty_name} is already teaching {sec} at {day_norm} P{target_period}"

        # 3. Section double-booking check
        if section_name:
            sec_key = (day_norm, target_period, section_name)
            if sec_key in self.section_index:
                existing = self.section_index[sec_key]
                if getattr(existing, "id", None) != entry_id:
                    sub = getattr(existing, "subject_code", getattr(existing, "subject", "Subject"))
                    return False, f"Section {section_name} is already scheduled for {sub} at {day_norm} P{target_period}"

        return True, None

