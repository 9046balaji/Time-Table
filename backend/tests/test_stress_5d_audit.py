import pytest
from httpx import AsyncClient, ASGITransport
from main import app
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.solver.diagnostics import InfeasibilityDiagnosticAnalyzer
from backend.solver.incremental_validator import ScheduleIndexStore
from backend.solver.csat_solver import SolverConfig

from app.core.database import get_db

@pytest.mark.asyncio
async def test_dimension1_database_integrity_and_versioning(async_db_session):
    """Dimension 1: Versioning and DB API Response Integrity."""
    async def override_get_db():
        yield async_db_session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/timetable/versions")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dimension2_solver_infeasibility_and_preflight():
    """Dimension 2: Preflight Analyzer Blocks Over-Subscribed Inputs."""
    config = SolverConfig()
    analyzer = InfeasibilityDiagnosticAnalyzer(solver_config=config)
    report = analyzer.analyze_infeasibility(
        sections=[{"id": 1, "strength": 90}],  # 90 strength exceeds largest 60 capacity room
        section_subjects=[],
        rooms=[{"id": 1, "capacity": 60}],
        time_slots=[{"day": "MON", "period": 1}],
        faculty_subject_map={}
    )
    diagnostics = report.get("diagnostics", [])
    assert len(diagnostics) >= 1
    assert diagnostics[0]["constraint_id"] == "HC-05"


@pytest.mark.asyncio
async def test_dimension3_concurrency_and_incremental_validation():
    """Dimension 3: Concurrent Slot Update and Incremental Lock Validation."""
    store = ScheduleIndexStore()
    entries = [
        {
            "id": "101",
            "section": "II AIML-A",
            "subject": "DS",
            "faculty": "Dr. S.Srikantha Reddy",
            "room": "619",
            "day": "MON",
            "period": 1
        }
    ]
    store.index_timetable(entries)
    
    # Test collision move detection
    res = store.validate_move(
        entry_id="102",
        section_name="II AIML-B",
        faculty_names=["Dr. S.Srikantha Reddy"],
        target_day="MON",
        target_period=1,
        target_room_code="604"
    )
    assert res["is_valid"] is False
    assert res["clash_type"] == "FACULTY"



@pytest.mark.asyncio
async def test_dimension4_api_contracts():
    """Dimension 4: API Contract Uniformity across Endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Check telemetry
        res = await client.get("/api/v1/telemetry/metrics")
        assert res.status_code == 200
        json_data = res.json()
        assert "database" in json_data
        assert json_data["database"]["total_sections"] == 60

@pytest.mark.asyncio
async def test_dimension5_publishing_and_export_integrity():
    """Dimension 5: Export Service Payload & Document Generation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/testing/export/excel?dataset=v5_ground_truth")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
