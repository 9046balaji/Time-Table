import pytest
from app.services.substitute_dispatcher import SubstituteDispatcher


@pytest.mark.asyncio
async def test_find_candidate_substitutes(async_db_session):
    result = await SubstituteDispatcher.find_candidate_substitutes(
        db=async_db_session,
        faculty_name="Dr. S. Srikantha Reddy",
        day="MON",
        period=1,
        subject_code="DS",
        version_id=5
    )
    assert "candidates" in result
    assert result["total_candidates"] > 0
    assert result["absent_faculty"] == "Dr. S. Srikantha Reddy"
    # Verify candidate structure
    top = result["candidates"][0]
    assert "id" in top
    assert "name" in top
    assert "suitability_score" in top
    assert "is_eligible" in top
    assert top["suitability_score"] >= 0


@pytest.mark.asyncio
async def test_substitute_dispatch_validation(async_db_session):
    # Test invalid entry id raises error
    with pytest.raises(ValueError, match="not found"):
        await SubstituteDispatcher.dispatch_substitute(
            db=async_db_session,
            session_id=1,
            entry_id=999999,
            substitute_faculty_id=1,
            reason="Test"
        )
