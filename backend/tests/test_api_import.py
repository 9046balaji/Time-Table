import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
V5_CANDIDATES = [
    os.path.join(ROOT_DIR, "time_table", "ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx"),
    "time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx",
    "../time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx",
]
V5_FILE_PATH = next((p for p in V5_CANDIDATES if os.path.exists(p)), V5_CANDIDATES[0])


def test_import_excel_api():
    assert os.path.exists(V5_FILE_PATH), f"V5 file missing at {V5_FILE_PATH}"

    with open(V5_FILE_PATH, "rb") as f:
        response = client.post(
            "/api/v1/import/excel",
            files={"file": ("ACSE_TIMETABLE_V5.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

    assert response.status_code == 200, f"Import endpoint failed: {response.text}"
    data = response.json()

    print("\n--- Import Excel API Response ---")
    print("Filename:", data["filename"])
    print("Total Sections:", data["total_sections"])
    print("Total Slots:", data["total_slots"])
    print("Hard Violations:", data["hard_violations"])
    print("Room Clashes:", data["room_clashes"])
    print("Faculty Clashes:", data["faculty_clashes"])

    assert data["total_sections"] >= 40
    assert data["total_slots"] >= 1000
    assert data["room_clashes"] > 0
    # V5 contains exactly one real faculty double-booking (Ms.G.Jyostna, THU P6,
    # IOT in two rooms). This asserted 0 only while the parser left faculty_list
    # empty, which made HC-02 unable to see any instructor at all.
    assert data["faculty_clashes"] == 1
    # clash_details also carries informational joint-section rows, so compare
    # only the entries flagged as real violations.
    violations = [d for d in data["clash_details"] if d.get("is_violation", True)]
    assert len(violations) == data["hard_violations"]
    assert data["physical_room_clashes"] == 7
    assert data["joint_section_slots"] == 62


if __name__ == "__main__":
    test_import_excel_api()
