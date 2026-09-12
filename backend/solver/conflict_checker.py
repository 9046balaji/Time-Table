import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Set, Tuple, Optional
from backend.solver.constraints import ConstraintRules


def faculty_identity_key(raw: Any) -> str:
    """
    Collapses a raw faculty name into a canonical identity key.

    HC-02 (faculty double-booking) must treat "DR. P. KALPANA", "DR. P. Kalpana"
    and "Dr.P.Kalpana" as the same human being. Grouping on the raw string lets a
    genuine double-booking pass validation whenever the two rows spell the name
    differently, so every faculty index in this module keys on this function.
    Display strings keep their original spelling.
    """
    if not raw:
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(raw).upper())


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
    # False for informational rows (joint-section teaching), which are reported
    # for transparency but are not hard-constraint violations.
    is_violation: bool = True


@dataclass
class ClashReport:
    room_clashes: int = 0
    physical_room_clashes: int = 0
    joint_section_slots: int = 0
    faculty_clashes: int = 0
    student_clashes: int = 0
    break_clashes: int = 0
    capacity_clashes: int = 0
    room_type_clashes: int = 0
    lab_continuity_clashes: int = 0
    special_slot_clashes: int = 0
    total_hard_violations: int = 0
    details: List[ClashDetail] = field(default_factory=list)


class ConflictChecker:
    """
    High-performance conflict analysis engine.
    Analyzes timetable entries to detect HC-01 (Room), HC-02 (Faculty), HC-03 (Student/Section), and HC-07 (Break) conflicts.
    """

    IGNORED_ROOM_CODES: Set[str] = ConstraintRules.IGNORED_ROOM_CODES

    @staticmethod
    def _get_attr(slot: Any, key: str, default: Any = None) -> Any:
        if isinstance(slot, dict):
            val = slot.get(key)
            return val if val is not None else default
        return getattr(slot, key, default)

    def detect(self, parsed_result: Any, check_extended_rules: bool = False) -> ClashReport:
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
        faculty_display: Dict[Tuple[str, int, str], str] = {}
        section_map: Dict[Tuple[str, int, str], List[Any]] = {}

        for slot in slots:
            period = self._get_attr(slot, "period", None)
            if period is None or period <= 0:
                continue

            day_norm = ConstraintRules.normalize_string(self._get_attr(slot, "day", ""))
            if not day_norm:
                continue

            section = self._get_attr(slot, "section", "") or ""
            subject_code = self._get_attr(slot, "subject_code", "") or self._get_attr(slot, "subject", "") or ""
            subject_type = self._get_attr(slot, "subject_type", "") or self._get_attr(slot, "type", "") or ""
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
            # Extended Rule Checking (HC-05, HC-06, HC-09, HC-10)
            # ---------------------------------------------------------
            if check_extended_rules:
                room_code = ConstraintRules.normalize_string(self._get_attr(slot, "room", ""))
                # HC-06 Room Type: Lab in classroom
                if (subject_type in ("P", "LAB") or code_norm in ConstraintRules.LAB_SUBJECTS) and room_code in ConstraintRules.CLASSROOM_ROOMS:
                    report.room_type_clashes += 1
                    report.details.append(
                        ClashDetail(
                            clash_type="ROOM_TYPE",
                            day=day_norm,
                            period=period,
                            key=room_code,
                            section_a=section,
                            subject_a=subject_code,
                            section_b="N/A",
                            subject_b="N/A",
                            message=f"[ROOM_TYPE_CLASH] Lab subject {subject_code} scheduled in classroom {room_code}",
                        )
                    )

                # HC-09 Special slots (Minors/Honors)
                if code_norm in ("MINORSHONORS", "MINORS", "HONORS"):
                    if not (day_norm in ("WED", "THU") and period in (7, 8)):
                        report.special_slot_clashes += 1

                # HC-10 4th Year SL/EL block
                if ("SL" in code_norm or "EL" in code_norm) and "IV" in section:
                    if period not in (1, 2) and not (day_norm == "SAT" and period in (6, 7, 8)):
                        report.special_slot_clashes += 1


            # ---------------------------------------------------------
            # 1. Bucket Room Occupancy (HC-01)
            # ---------------------------------------------------------
            room = ConstraintRules.normalize_string(self._get_attr(slot, "room", ""))
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
            faculty_list = self._get_attr(slot, "faculty_list", None)
            if not faculty_list:
                facs = self._get_attr(slot, "faculty", [])
                if isinstance(facs, str):
                    faculty_list = [f.strip() for f in facs.split(",") if f.strip()]
                elif isinstance(facs, list):
                    faculty_list = [str(f).strip() for f in facs if str(f).strip()]

            if faculty_list:
                for fac in faculty_list:
                    fac_id = faculty_identity_key(fac)
                    if fac_id:
                        fac_key = (day_norm, period, fac_id)
                        if fac_key not in faculty_map:
                            faculty_map[fac_key] = []
                            faculty_display[fac_key] = str(fac).strip()
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
            distinct_slots_by_section: Dict[str, Any] = {}
            for s in occupied_slots:
                sec = self._get_attr(s, "section", "")
                if sec not in distinct_slots_by_section:
                    distinct_slots_by_section[sec] = s

            conflicting_slots = list(distinct_slots_by_section.values())
            if len(conflicting_slots) > 1:
                for i in range(len(conflicting_slots)):
                    for j in range(i + 1, len(conflicting_slots)):
                        sa, sb = conflicting_slots[i], conflicting_slots[j]
                        report.room_clashes += 1

                        sub_a_code = self._get_attr(sa, "subject_code", "") or self._get_attr(sa, "subject", "") or ""
                        sub_b_code = self._get_attr(sb, "subject_code", "") or self._get_attr(sb, "subject", "") or ""
                        sub_a_norm = ConstraintRules.normalize_string(sub_a_code).replace("(P)", "").replace("(T)", "").replace("(L)", "").strip()
                        sub_b_norm = ConstraintRules.normalize_string(sub_b_code).replace("(P)", "").replace("(T)", "").replace("(L)", "").strip()

                        # Two sections share a room legitimately only when they are
                        # provably in the same class. If either subject is unknown we
                        # cannot prove that, so fail safe and report a real clash
                        # rather than silently excusing it as joint teaching.
                        is_physical_clash = (
                            not sub_a_norm or not sub_b_norm or sub_a_norm != sub_b_norm
                        )
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
                                section_a=self._get_attr(sa, "section", ""),
                                subject_a=sub_a_code,
                                section_b=self._get_attr(sb, "section", ""),
                                subject_b=sub_b_code,
                                message=f"[{clash_label}] {day} Period-{period}, Room {room} → {self._get_attr(sa, 'section', '')}: {sub_a_code} AND {self._get_attr(sb, 'section', '')}: {sub_b_code}",
                                is_violation=is_physical_clash,
                            )
                        )

        # =============================================================
        # Process Faculty Clashes (HC-02)
        # =============================================================
        for _fac_key, occupied_slots in faculty_map.items():
            day, period, _fac_id = _fac_key
            fac = faculty_display.get(_fac_key, _fac_id)
            if len(occupied_slots) <= 1:
                continue

            distinct_slots_by_section = {}
            for s in occupied_slots:
                sec = self._get_attr(s, "section", "")
                if sec not in distinct_slots_by_section:
                    distinct_slots_by_section[sec] = s

            conflicting_slots = list(distinct_slots_by_section.values())
            if len(conflicting_slots) > 1:
                for i in range(len(conflicting_slots)):
                    for j in range(i + 1, len(conflicting_slots)):
                        sa, sb = conflicting_slots[i], conflicting_slots[j]
                        report.faculty_clashes += 1
                        sub_a_code = self._get_attr(sa, "subject_code", "") or self._get_attr(sa, "subject", "") or ""
                        sub_b_code = self._get_attr(sb, "subject_code", "") or self._get_attr(sb, "subject", "") or ""
                        report.details.append(
                            ClashDetail(
                                clash_type="FACULTY",
                                day=day,
                                period=period,
                                key=fac,
                                section_a=self._get_attr(sa, "section", ""),
                                subject_a=sub_a_code,
                                section_b=self._get_attr(sb, "section", ""),
                                subject_b=sub_b_code,
                                message=f"[FACULTY_CLASH] {day} Period-{period}, Faculty {fac} → {self._get_attr(sa, 'section', '')}: {sub_a_code} AND {self._get_attr(sb, 'section', '')}: {sub_b_code}",
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

        # room_clashes counts every room overlap, including joint-section teaching
        # (two sections taking the same subject together in one room), which is
        # legitimate and not a violation. On the V5 baseline 62 of 69 overlaps are
        # joint sections, so counting them here made the consensus VALIDATOR veto
        # schedules that are actually valid. Only physical clashes are violations.
        report.total_hard_violations = (
            report.physical_room_clashes
            + report.faculty_clashes
            + report.student_clashes
            + report.break_clashes
        )
        if check_extended_rules:
            report.total_hard_violations += (
                report.capacity_clashes
                + report.room_type_clashes
                + report.lab_continuity_clashes
                + report.special_slot_clashes
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
                    fac_id = faculty_identity_key(fac)
                    if fac_id:
                        self.faculty_index[(day, period, fac_id)] = e

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
            fac_clean = faculty_identity_key(faculty_name)
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

