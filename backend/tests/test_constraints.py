import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.solver.constraints import ConstraintRules
from backend.solver.conflict_checker import ConflictChecker, IncrementalValidator
from backend.parser.excel_parser import ParsedSlot, ParsedResult


def test_hc01_room_conflict_detection():
    """HC-01: Detect when two different sections/subjects occupy the same physical room at the exact same time."""
    checker = ConflictChecker()

    slot1 = ParsedSlot(section="SEC-A", day="MON", period=1, subject_code="DS", room="604", subject_type="L")
    slot2 = ParsedSlot(section="SEC-B", day="MON", period=1, subject_code="DBMS", room="604", subject_type="L")

    result = ParsedResult(
        total_sections=2,
        total_slots=2,
        sections={"SEC-A": [slot1], "SEC-B": [slot2]},
        raw_entries=[slot1, slot2]
    )

    report = checker.detect(result)
    assert report.room_clashes >= 1, "Expected room clash to be detected for same room/period"
    assert report.physical_room_clashes == 1


def test_hc02_faculty_conflict_detection():
    """HC-02: Detect when a single faculty member is assigned to two different classes at the same time."""
    checker = ConflictChecker()

    slot1 = ParsedSlot(section="SEC-A", day="MON", period=1, subject_code="DS", room="604", subject_type="L", faculty_list=["Dr. Smith"])
    slot2 = ParsedSlot(section="SEC-B", day="MON", period=1, subject_code="DBMS", room="605", subject_type="L", faculty_list=["Dr. Smith"])

    result = ParsedResult(
        total_sections=2,
        total_slots=2,
        sections={"SEC-A": [slot1], "SEC-B": [slot2]},
        raw_entries=[slot1, slot2]
    )

    report = checker.detect(result)
    assert report.faculty_clashes >= 1, "Expected faculty clash to be detected for double-booked faculty"


def test_hc03_student_section_conflict_detection():
    """HC-03: Detect when a section is double-booked in two different rooms at the exact same time."""
    checker = ConflictChecker()

    slot1 = ParsedSlot(section="SEC-A", day="MON", period=1, subject_code="DS", room="604", subject_type="L")
    slot2 = ParsedSlot(section="SEC-A", day="MON", period=1, subject_code="DBMS", room="605", subject_type="L")

    result = ParsedResult(
        total_sections=1,
        total_slots=2,
        sections={"SEC-A": [slot1, slot2]},
        raw_entries=[slot1, slot2]
    )

    report = checker.detect(result)
    assert report.student_clashes == 1, "Expected student section clash to be detected for double-booked section"


def test_hc07_break_slot_conflict_detection():
    """HC-07: Detect when a class is scheduled during a break slot."""
    checker = ConflictChecker()

    slot1 = ParsedSlot(section="SEC-A", day="MON", period=3, subject_code="DS", room="604", subject_type="BREAK")

    result = ParsedResult(
        total_sections=1,
        total_slots=1,
        sections={"SEC-A": [slot1]},
        raw_entries=[slot1]
    )

    report = checker.detect(result)
    assert report.break_clashes == 1, "Expected break clash to be detected"


def test_hc06_room_type_compatibility():
    """HC-06: Check lab vs classroom room type compatibility."""
    assert ConstraintRules.is_room_compatible("P", "computer_lab") is True
    assert ConstraintRules.is_room_compatible("P", "gpu_lab") is True
    assert ConstraintRules.is_room_compatible("L", "classroom") is True


def test_hc07_break_block_protection():
    """HC-07: Verify break slot detection."""
    assert ConstraintRules.is_break_slot(3, "BREAK") is True
    assert ConstraintRules.is_break_slot(5, "LUNCH") is True
    assert ConstraintRules.is_break_slot(1, "LECTURE") is False


def test_hc08_lab_consecutiveness_rules():
    """HC-08: Verify lab pair validity and break guard rules."""
    assert ConstraintRules.is_valid_lab_pair(1, 2, "MON") is True
    assert ConstraintRules.is_valid_lab_pair(2, 3, "MON") is False
    assert ConstraintRules.is_valid_lab_pair(1, 2, "SAT") is False


def test_hc09_faculty_daily_cap():
    """HC-09: Verify faculty daily teaching cap (max 5 classes/day)."""
    assert ConstraintRules.check_faculty_daily_cap(4, max_cap=5) is True
    assert ConstraintRules.check_faculty_daily_cap(5, max_cap=5) is True
    assert ConstraintRules.check_faculty_daily_cap(6, max_cap=5) is False


def test_hc10_continuous_teaching_limit():
    """HC-10: Verify max continuous teaching hours (max 4 consecutive periods)."""
    assert ConstraintRules.check_continuous_teaching_limit(3, max_consecutive=4) is True
    assert ConstraintRules.check_continuous_teaching_limit(4, max_consecutive=4) is True
    assert ConstraintRules.check_continuous_teaching_limit(5, max_consecutive=4) is False


def test_incremental_validator():
    """Verify O(1) IncrementalValidator for fast drag-and-drop validation."""
    slot1 = ParsedSlot(section="SEC-A", day="MON", period=1, subject_code="DS", room="604", faculty_list=["Dr. Smith"])
    setattr(slot1, "id", 1)
    validator = IncrementalValidator([slot1])

    # Valid move to an empty slot
    valid, msg = validator.validate_move(entry_id=2, target_day="MON", target_period=2, target_room="605", faculty_name="Dr. Jones", section_name="SEC-B")
    assert valid is True
    assert msg is None

    # Invalid room collision
    valid, msg = validator.validate_move(entry_id=2, target_day="MON", target_period=1, target_room="604")
    assert valid is False
    assert "occupied by SEC-A" in msg

    # Invalid faculty double-booking
    valid, msg = validator.validate_move(entry_id=2, target_day="MON", target_period=1, target_room="605", faculty_name="Dr. Smith")
    assert valid is False
    assert "Dr. Smith is already teaching" in msg


