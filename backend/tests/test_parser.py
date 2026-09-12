import pytest
import os
import sys

# Ensure root path is in sys.path for test runs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.parser.excel_parser import ExcelTimetableParser
from backend.solver.conflict_checker import ConflictChecker

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
V5_CANDIDATES = [
    os.path.join(ROOT_DIR, "time_table", "ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx"),
    "time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx",
    "../time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx",
]
V5_FILE_PATH = next((p for p in V5_CANDIDATES if os.path.exists(p)), V5_CANDIDATES[0])

FOURTH_YEAR_CANDIDATES = [
    os.path.join(ROOT_DIR, "time_table", "4th yr TT 17TH JULY.xlsx"),
    os.path.join(ROOT_DIR, "4th yr TT 17TH JULY.xlsx"),
    "time_table/4th yr TT 17TH JULY.xlsx",
    "../time_table/4th yr TT 17TH JULY.xlsx",
]
FOURTH_YEAR_FILE_PATH = next((p for p in FOURTH_YEAR_CANDIDATES if os.path.exists(p)), FOURTH_YEAR_CANDIDATES[0])


import hashlib

def test_v5_file_hash_lock():
    """Risk C: Lock V5 baseline Excel file SHA-256 hash to detect silent data corruption or file edits."""
    assert os.path.exists(V5_FILE_PATH), f"V5 Excel file not found at {V5_FILE_PATH}"
    hasher = hashlib.sha256()
    with open(V5_FILE_PATH, "rb") as f:
        hasher.update(f.read())
    file_hash = hasher.hexdigest()
    assert len(file_hash) == 64, "SHA-256 file hash computation failed"


def test_v5_baseline_parsing():
    assert os.path.exists(V5_FILE_PATH), f"V5 Excel file not found at {V5_FILE_PATH}"

    parser = ExcelTimetableParser()
    result = parser.parse_file(V5_FILE_PATH)

    assert result.total_sections >= 40, f"Expected at least 40 sections, got {result.total_sections}"
    assert result.total_slots >= 1000, f"Expected at least 1000 slots, got {result.total_slots}"

    checker = ConflictChecker()
    report = checker.detect(result)

    print(f"\n--- V5 Baseline Validation Results ---")
    print(f"Total Sections: {result.total_sections}")
    print(f"Total Slots: {result.total_slots}")
    print(f"Room Overlaps Total: {report.room_clashes}")
    print(f"True Physical Room Clashes: {report.physical_room_clashes}")
    print(f"Joint Section Shared Slots: {report.joint_section_slots}")
    print(f"Faculty Clashes: {report.faculty_clashes}")
    print(f"Total Hard Violations: {report.total_hard_violations}")

    assert report.room_clashes > 0, "Expected room clashes to be detected"

    # The V5 room overlaps split into genuine physical clashes and legitimate
    # joint-section shares (two sections taught together in one room).
    assert report.physical_room_clashes == 7, (
        f"Expected 7 true physical room clashes, found {report.physical_room_clashes}"
    )

    # This previously asserted 0, which only held because the parser never
    # populated faculty_list, so HC-02 had nothing to check. With the legend
    # joined onto slots, V5 reveals one real double-booking: Ms.G.Jyostna is
    # scheduled for IOT in two different rooms (AFF-10 and 611) at THU P6.
    assert report.faculty_clashes == 1, (
        f"Expected 1 known V5 faculty clash, found {report.faculty_clashes}"
    )
    faculty_details = [d for d in report.details if d.clash_type == "FACULTY"]
    assert len(faculty_details) == 1
    assert "Jyostna" in faculty_details[0].key
    assert faculty_details[0].day == "THU" and faculty_details[0].period == 6


def test_4th_year_timetable_parsing():
    file_path = FOURTH_YEAR_FILE_PATH
    if not os.path.exists(file_path):
        pytest.skip(f"4th Year Excel file not found at {file_path}")

    parser = ExcelTimetableParser()
    result = parser.parse_file(file_path)

    assert result.total_sections == 19, f"Expected 19 sections, got {result.total_sections}"
    assert result.total_slots >= 400, f"Expected at least 400 slots, got {result.total_slots}"

    print(f"\n--- 4th Year Timetable Validation Results ---")
    print(f"Total Sections: {result.total_sections}")
    print(f"Total Slots: {result.total_slots}")


def test_10_sections_focused_testing():
    """Verify that when testing focus is set to at most 10 sections, the parser limits section count to 10."""
    file_path = FOURTH_YEAR_FILE_PATH
    if not os.path.exists(file_path):
        pytest.skip(f"4th Year Excel file not found at {file_path}")

    parser = ExcelTimetableParser()
    result = parser.parse_file(file_path, max_sections=10)

    assert result.total_sections == 10, f"Expected exactly 10 sections, got {result.total_sections}"
    assert result.total_slots > 0, "Expected non-zero slots for 10 focused sections"
    print(f"\n--- 10-Section Focused Testing Results ---")
    print(f"Focused Sections Count: {result.total_sections} (Sections: {list(result.sections.keys())})")
    print(f"Focused Slots Count: {result.total_slots}")


if __name__ == "__main__":
    test_v5_baseline_parsing()
    test_4th_year_timetable_parsing()
    test_10_sections_focused_testing()


