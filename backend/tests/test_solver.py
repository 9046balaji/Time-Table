import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.solver.csat_solver import CPSATSolver, SolverConfig


def test_cp_sat_solver_basic():
    sections = [
        {"id": 1, "name": "II AIML-A"},
        {"id": 2, "name": "II AIML-B"},
    ]
    section_subjects = [
        {"section_id": 1, "subject_id": 101, "total_slots_needed": 3},
        {"section_id": 1, "subject_id": 102, "total_slots_needed": 3},
        {"section_id": 2, "subject_id": 101, "total_slots_needed": 3},
        {"section_id": 2, "subject_id": 102, "total_slots_needed": 3},
    ]
    rooms = [
        {"id": 1, "code": "601", "type": "classroom"},
        {"id": 2, "code": "602", "type": "classroom"},
    ]
    # Provide 7 usable periods + 1 blocked lunch period
    time_slots = [
        {"id": 1, "day": "MON", "period": 1, "is_blocked": False},
        {"id": 2, "day": "MON", "period": 2, "is_blocked": False},
        {"id": 3, "day": "MON", "period": 3, "is_blocked": False},
        {"id": 4, "day": "MON", "period": 4, "is_blocked": False},
        {"id": 5, "day": "MON", "period": 5, "is_blocked": False},
        {"id": 6, "day": "MON", "period": 6, "is_blocked": True},  # Lunch
        {"id": 7, "day": "MON", "period": 7, "is_blocked": False},
        {"id": 8, "day": "MON", "period": 8, "is_blocked": False},
    ]

    solver = CPSATSolver(config=SolverConfig(timeout_seconds=10))
    result = solver.solve(sections, section_subjects, rooms, time_slots)

    print("\n--- CP-SAT Solver Test Result ---")
    print("Status:", result["status"])
    print("Runtime:", result["runtime_seconds"], "s")
    print("Entries Scheduled:", result["entries_count"])

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert result["hard_violations"] == 0
    assert result["entries_count"] == 12  # 2 sections x 6 slots needed
    # Verify no entries assigned to blocked period 6
    p6_entries = [e for e in result["entries"] if e["time_slot_id"] == 6]
    assert len(p6_entries) == 0, "No classes should be scheduled in blocked period"


if __name__ == "__main__":
    test_cp_sat_solver_basic()
