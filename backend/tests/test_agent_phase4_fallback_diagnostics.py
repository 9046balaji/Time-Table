import pytest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.solver.csat_solver import CPSATSolver
from app.services.tool_registry import ToolRegistry


def test_phase4_multi_stage_repair_fallback():
    solver = CPSATSolver()
    current_entries = [
        {"id": "1", "section": "SEC-A", "day": "MON", "period": 1, "room": "604", "faculty": ["Dr. Reddy"], "type": "LAB"}
    ]
    available_rooms = [
        {"code": "604", "room_type": "lab", "capacity": 60},
        {"code": "605", "room_type": "lab", "capacity": 60}
    ]

    res = solver.solve_local_repair(
        current_entries=current_entries,
        available_rooms=available_rooms,
        disrupted_room_code="604"
    )

    assert res["status"] == "OPTIMAL"
    assert res["moved_count"] == 1
    assert res["entries"][0]["room"] == "605"
    assert "repair_stage" in res["entries"][0]


@pytest.mark.asyncio
async def test_phase4_explain_infeasibility_tool():
    # Feasible entries
    feasible = [{"id": "1", "section": "SEC-A", "day": "MON", "period": 1, "room": "601", "faculty": ["Dr. Reddy"]}]
    f_res = await ToolRegistry.explain_infeasibility(feasible)
    assert f_res["is_infeasible"] is False

    # Infeasible entries with room clash
    infeasible = [
        {"id": "1", "section": "SEC-A", "day": "MON", "period": 1, "room": "601", "faculty": ["Dr. Reddy"]},
        {"id": "2", "section": "SEC-B", "day": "MON", "period": 1, "room": "601", "faculty": ["P. Girija"]}
    ]
    inf_res = await ToolRegistry.explain_infeasibility(infeasible)
    assert inf_res["is_infeasible"] is True
    assert inf_res["room_clashes"] == 1
    assert "HC-01 Room Conflict" in inf_res["diagnostic_summary"]
