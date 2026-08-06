import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.solver.constraints import ConstraintRules
from backend.solver.conflict_checker import ConflictChecker
from backend.parser.excel_parser import ParsedSlot, ParsedResult


def test_hc01_room_conflict_detection():
    """HC-01: Detect when two different sections/subjects occupy the same physical room at the exact same time."""
    checker = ConflictChecker()

    # Conflict: Sec A and Sec B in Room 604 on MON Period 1
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
    # Valid lab pair: P1 & P2 on Monday
    assert ConstraintRules.is_valid_lab_pair(1, 2, "MON") is True
    # Invalid: Break guard pair (P2, P3) spans tea break
    assert ConstraintRules.is_valid_lab_pair(2, 3, "MON") is False
    # Invalid: Saturday labs
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
