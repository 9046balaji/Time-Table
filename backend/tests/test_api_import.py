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
    assert data["faculty_clashes"] == 0
    assert len(data["clash_details"]) == data["hard_violations"]


if __name__ == "__main__":
    test_import_excel_api()
