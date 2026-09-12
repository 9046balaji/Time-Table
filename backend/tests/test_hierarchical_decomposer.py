import pytest
from app.solver.hierarchical_decomposer import HierarchicalDecomposer


@pytest.mark.asyncio
async def test_hierarchical_decomposition(async_db_session):
    result = await HierarchicalDecomposer.solve_hierarchically(
        db=async_db_session,
        version_id=5,
        timeout_seconds=10
    )
    assert result["status"] == "COMPLETED"
    assert result["total_slots"] > 0
    assert result["macro_locked_slots"] >= 0
    assert result["micro_solved_slots"] > 0
    assert "entries" in result
