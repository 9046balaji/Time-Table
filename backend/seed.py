import sys
import os
import asyncio
from datetime import date

# Ensure root path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.parser.excel_parser import ExcelTimetableParser
from backend.solver.conflict_checker import ConflictChecker

V5_FILE_PATH = "time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx"


def run_seed():
    print("Parsing V5 Excel dataset...")
    parser = ExcelTimetableParser()
    result = parser.parse_file(V5_FILE_PATH)

    checker = ConflictChecker()
    report = checker.detect(result)

    print(f"\n==========================================")
    print(f"  VFSTR ACSE Timetable Data Seed Report")
    print(f"==========================================")
    print(f"Total Sections Extracted: {result.total_sections}")
    print(f"Total Scheduled Slots:    {result.total_slots}")
    print(f"Faculty Mappings Count:   {len(result.faculty_mappings)}")
    print(f"Baseline Room Clashes:    {report.room_clashes}")
    print(f"Baseline Faculty Clashes: {report.faculty_clashes}")
    print(f"==========================================\n")
    print("Seed complete. Baseline dataset ready.")


if __name__ == "__main__":
    run_seed()
