import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.multi_agent_consensus import MultiAgentConsensusEngine
from backend.solver.csat_solver import CPSATSolver


@pytest.mark.asyncio
async def test_phase8_solver_policy_alignment_and_priority():
    # Test SC-07 policy alignment in SOLVER consensus
    entries = [
        {"id": "1", "section": "SEC-A", "day": "MON", "period": 1, "room": "601", "faculty": ["Dr. Reddy"], "subject": "DS"},
        {"id": "2", "section": "SEC-A", "day": "MON", "period": 2, "room": "601", "faculty": ["P. Girija"], "subject": "AI"}
    ]
    rooms = [{"code": "601", "room_type": "classroom", "capacity": 60}]

    from app.core.database import ensure_database, AsyncSessionLocal
    from app.models.agent import AgentSession
    await ensure_database()
    async with AsyncSessionLocal() as db:
        sess = AgentSession(goal="Test Phase 8", status="active", current_step="observe")
        db.add(sess)
        await db.commit()
        await db.refresh(sess)
        res = await MultiAgentConsensusEngine.evaluate_consensus(db=db, session_id=sess.id, timetable_entries=entries)
    solver_vote = next(v for v in res["votes"] if v["role"] == "SOLVER")
    assert solver_vote["policy_rule"] == "SC-07"
    assert solver_vote["vote"] == "APPROVE"

    # Test priority taxonomy in CPSATSolver
    solver = CPSATSolver()
    repair = solver.solve_local_repair(
        current_entries=entries,
        available_rooms=rooms,
        disrupted_room_code="601",
        priority_level="P1_CRITICAL"
    )
    assert repair["status"] == "OPTIMAL"
