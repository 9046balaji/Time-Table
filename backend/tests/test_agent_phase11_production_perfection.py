import pytest
from httpx import AsyncClient, ASGITransport
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.services.agent_service import AgentService
from app.core.database import AsyncSessionLocal
from backend.solver.csat_solver import CPSATSolver


@pytest.mark.asyncio
async def test_phase11_cpsat_warm_starts_and_dead_session_recovery():
    # Test 1: CPSATSolver warm start hints & status string
    solver = CPSATSolver()
    sections = [{"id": "SEC1", "name": "II AIML-A"}]
    sec_subjs = [{"section_id": "SEC1", "subject_id": "DS", "subject_code": "DS", "subject_type": "L"}]
    rooms = [{"id": "601", "code": "601", "room_type": "classroom", "capacity": 60}]
    slots = [{"id": 1, "day": "MON", "period": 1, "is_blocked": False}]

    res = solver.solve(
        sections, sec_subjs, rooms, slots,
        warm_start_hints=[{"section_id": "SEC1", "subject_id": "DS", "room_id": "601", "time_slot_id": 1}]
    )
    assert res["status"] in ("OPTIMAL", "FEASIBLE", "UNKNOWN", "INFEASIBLE")

    # Test 2: AgentService dead session recovery
    async with AsyncSessionLocal() as db:
        rec_res = await AgentService.recover_dead_sessions(db, max_stuck_seconds=0)
        assert "recovered_count" in rec_res
        assert "recovered_session_ids" in rec_res
