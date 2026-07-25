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
    assert report.faculty_clashes == 0, f"Expected 0 faculty clashes, found {report.faculty_clashes}"


if __name__ == "__main__":
    test_v5_baseline_parsing()
