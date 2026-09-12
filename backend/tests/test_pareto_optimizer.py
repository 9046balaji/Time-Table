import pytest
from app.services.pareto_optimizer import ParetoOptimizer


@pytest.mark.asyncio
async def test_pareto_evaluation(async_db_session):
    result = await ParetoOptimizer.evaluate_timetable(db=async_db_session, version_id=5)
    assert "objectives" in result
    assert "profile_scores" in result
    assert "faculty_fatigue_score" in result["objectives"]
    assert "student_gap_score" in result["objectives"]
    assert "campus_transit_score" in result["objectives"]
    assert "afternoon_load_score" in result["objectives"]

    # All profile scores should be between 0 and 100
    for p_key, p_data in result["profile_scores"].items():
        assert 0 <= p_data["composite_score"] <= 100


def test_evaluate_objectives_scoring():
    sample_entries = [
        {"section": "II AIML-A", "day": "MON", "period": 1, "faculty": "Dr. A", "room": "601"},
        {"section": "II AIML-A", "day": "MON", "period": 2, "faculty": "Dr. B", "room": "601"},
        {"section": "II AIML-A", "day": "MON", "period": 3, "faculty": "Dr. C", "room": "601"},
    ]
    objs = ParetoOptimizer.evaluate_objectives(sample_entries)
    assert objs["faculty_fatigue_score"] > 80
    assert objs["student_gap_score"] == 100.0
