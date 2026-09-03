import pytest
from httpx import AsyncClient, ASGITransport
try:
    from main import app
except ImportError:
    from app.main import app

from app.services.multi_agent_scheduler import (
    SectionCurriculumAgent,
    FacultyWorkloadAgent,
    VenueBlockAgent,
    TemporalFlowAgent,
    MasterArbiterAgent,
)
try:
    from backend.solver.constraints import ConstraintRules
except (ImportError, ModuleNotFoundError):
    from solver.constraints import ConstraintRules


@pytest.mark.asyncio
async def test_section_curriculum_agent_audit():
    # 1. Valid slots
    valid_slots = [
        {"section": "II AIML A", "day": "MON", "period": 1, "subject": "SFCDS", "type": "L"},
        {"section": "II AIML A", "day": "WED", "period": 7, "subject": "MINORS/HONORS", "type": "SPECIAL"},
        {"section": "II AIML A", "day": "THU", "period": 7, "subject": "MINORS/HONORS", "type": "SPECIAL"},
        {"section": "II AIML A", "day": "FRI", "period": 4, "subject": "LIBRARY", "type": "LIBRARY"},
    ]
    critiques = SectionCurriculumAgent.audit(valid_slots)
    # Shouldn't have any minors/honors or library hard vetoes
    hard_vetoes = [c for c in critiques if c.rule_id in ("HC-09_MINORS_HONORS", "LIBRARY_RULE")]
    assert len(hard_vetoes) == 0

    # 2. Invalid Minors/Honors placed on Monday period 1
    invalid_slots = [
        {"section": "II AIML A", "day": "MON", "period": 1, "subject": "MINORS/HONORS", "type": "SPECIAL"},
    ]
    critiques_invalid = SectionCurriculumAgent.audit(invalid_slots)
    minors_veto = [c for c in critiques_invalid if c.rule_id == "HC-09_MINORS_HONORS"]
    assert len(minors_veto) > 0


@pytest.mark.asyncio
async def test_faculty_workload_agent_fatigue():
    # Test daily teaching cap (exceeds 5 hours in one day)
    overworked_slots = [
        {"section": f"II AIML {chr(65+i)}", "day": "MON", "period": i+1, "subject": "SFCDS", "faculty": "Dr. P. Kalpana"}
        for i in range(6)
    ]
    critiques = FacultyWorkloadAgent.audit(overworked_slots)
    daily_veto = [c for c in critiques if c.rule_id == "HC-09_DAILY_CAP"]
    assert len(daily_veto) > 0

    # Test double booking
    double_booked_slots = [
        {"section": "II AIML A", "day": "TUE", "period": 2, "subject": "SFCDS", "faculty": "Dr. P. Kalpana"},
        {"section": "II AIML B", "day": "TUE", "period": 2, "subject": "SFCDS", "faculty": "Dr. P. Kalpana"},
    ]
    critiques_double = FacultyWorkloadAgent.audit(double_booked_slots)
    db_veto = [c for c in critiques_double if c.rule_id == "HC-02_DOUBLE_BOOKING"]
    assert len(db_veto) > 0


@pytest.mark.asyncio
async def test_venue_block_agent_and_gpu_priority():
    # Test Lab placed in non-lab classroom 601
    bad_room_slots = [
        {"section": "II AIML A", "day": "MON", "period": 1, "subject": "SFCDS(P)", "type": "P", "room": "601"}
    ]
    critiques = VenueBlockAgent.audit(bad_room_slots)
    room_type_veto = [c for c in critiques if c.rule_id == "HC-06_ROOM_TYPE"]
    assert len(room_type_veto) > 0

    # Test GPU subject DL in standard classroom vs GPU lab
    gpu_slots = [
        {"section": "III AIML A", "day": "WED", "period": 1, "subject": "DL(P)", "type": "P", "room": "604"}
    ]
    critiques_gpu = VenueBlockAgent.audit(gpu_slots)
    gpu_notice = [c for c in critiques_gpu if c.rule_id == "SC-06_GPU_PRIORITY"]
    assert len(gpu_notice) > 0


@pytest.mark.asyncio
async def test_temporal_flow_agent_and_breaks():
    # Lab span < 2
    single_period_lab = [
        {"section": "II AIML A", "day": "MON", "period": 1, "subject": "DS(P)", "type": "P", "spanPeriods": 1}
    ]
    critiques = TemporalFlowAgent.audit(single_period_lab)
    consec_critique = [c for c in critiques if c.rule_id == "HC-08_LAB_CONSECUTIVENESS"]
    assert len(consec_critique) > 0


@pytest.mark.asyncio
async def test_student_welfare_agent_cognitive_fatigue():
    from app.services.multi_agent_scheduler import StudentWelfareAgent
    overloaded_student_slots = [
        {"section": "II AIML A", "day": "MON", "period": p, "subject": "SFCDS"}
        for p in range(1, 9)
    ]
    critiques = StudentWelfareAgent.audit(overloaded_student_slots)
    fatigue_critiques = [c for c in critiques if c.rule_id == "STUDENT_COGNITIVE_OVERLOAD"]
    assert len(fatigue_critiques) > 0


@pytest.mark.asyncio
async def test_lab_tech_infra_agent_maintenance():
    from app.services.multi_agent_scheduler import LabTechInfraAgent
    sat_aftf_slots = [
        {"section": "III AIML A", "day": "SAT", "period": 7, "subject": "DL(P)", "room": "AFTF-12"}
    ]
    critiques = LabTechInfraAgent.audit(sat_aftf_slots)
    maint_critiques = [c for c in critiques if c.rule_id == "INFRA_MAINTENANCE_WINDOW"]
    assert len(maint_critiques) > 0


@pytest.mark.asyncio
async def test_multi_agent_api_audit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/api/v1/agent/multi-agent/audit?version_id=12")
        assert resp.status_code == 200
        data = resp.json()
        assert "votes" in data
        assert len(data["votes"]) == 7
        agent_names = {v["agent"] for v in data["votes"]}
        assert "SectionCurriculumAgent" in agent_names
        assert "FacultyWorkloadAgent" in agent_names
        assert "VenueBlockAgent" in agent_names
        assert "TemporalFlowAgent" in agent_names
        assert "StudentWelfareAgent" in agent_names
        assert "LabTechInfraAgent" in agent_names
        assert "ValidatorAgent" in agent_names


@pytest.mark.asyncio
async def test_multi_agent_api_sections():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/api/v1/agent/multi-agent/sections?version_id=12")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_sections" in data
        assert data["total_sections"] > 0
        assert "by_year" in data
        assert "II_YEAR" in data["by_year"]


@pytest.mark.asyncio
async def test_multi_agent_api_synthesize():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/api/v1/agent/multi-agent/synthesize", json={
            "version_id": 12,
            "max_rounds": 2,
            "scope": "II_YEAR",
            "user_directive": "Optimize II Year morning slots"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "votes" in data
        assert "dialogue_history" in data
        assert len(data["dialogue_history"]) > 0
        assert "summary" in data
