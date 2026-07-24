import pytest
from app.services.faculty_service import FacultyService
from app.services.section_service import SectionService
from app.services.room_service import RoomService
from app.services.timetable_service import TimetableService
from app.services.validate_service import ValidateService
from app.services.export_service import ExportService
from backend.solver.diagnostics import InfeasibilityDiagnosticAnalyzer
from backend.solver.conflict_checker import IncrementalValidator, ClashDetail
from backend.solver.csat_solver import SolverConfig


@pytest.mark.asyncio
async def test_faculty_service(async_db_session):
    res = await FacultyService.get_all_faculty(async_db_session)
    assert "items" in res
    assert res["count"] > 0
    assert any(f["name"] == "Dr. P. Kalpana" for f in res["items"])


@pytest.mark.asyncio
async def test_section_service(async_db_session):
    res = await SectionService.list_sections(async_db_session)
    assert "items" in res
    assert res["total"] == 44
    assert any(s["name"] == "II AIML-A" for s in res["items"])


@pytest.mark.asyncio
async def test_room_service(async_db_session):
    res = await RoomService.list_rooms(async_db_session)
    assert "items" in res
    assert res["total"] == 35
    assert any(r["code"] == "601" for r in res["items"])


@pytest.mark.asyncio
async def test_timetable_service(async_db_session):
    res = await TimetableService.get_version_timetable(async_db_session, version_id=5)
    assert res["version_id"] == 5
    assert "entries" in res


@pytest.mark.asyncio
async def test_validate_service(async_db_session):
    res = await ValidateService.validate_timetable(async_db_session, version_id=5)
    assert res["hard_violations"] == 51
    assert res["status"] == "NEEDS_FIX"


@pytest.mark.asyncio
async def test_export_service():
    excel_bytes = await ExportService.generate_excel_export()
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0

    section_pdf_bytes = await ExportService.generate_section_pdfs()
    assert isinstance(section_pdf_bytes, bytes)
    assert section_pdf_bytes.startswith(b"%PDF")

    faculty_pdf_bytes = await ExportService.generate_faculty_pdfs()
    assert isinstance(faculty_pdf_bytes, bytes)
    assert faculty_pdf_bytes.startswith(b"%PDF")


def test_incremental_validator():
    class MockEntry:
        def __init__(self, id, day, period, room, section, subject, faculty):
            self.id = id
            self.day = day
            self.period = period
            self.room = room
            self.section = section
            self.subject = subject
            self.faculty = faculty

    entries = [
        MockEntry(1, "MON", 1, "601", "II AIML-A", "DS", ["Dr. Reddy"]),
        MockEntry(2, "MON", 1, "602", "II AIML-B", "AI", ["P. Girija"]),
    ]

    validator = IncrementalValidator(entries)
    # Valid move into empty room 603
    valid, msg = validator.validate_move(1, "MON", 1, "603", "Dr. Reddy")
    assert valid is True
    assert msg is None

    # Invalid move into occupied room 602
    valid, msg = validator.validate_move(1, "MON", 1, "602", "Dr. Reddy")
    assert valid is False
    assert "Room 602 is occupied" in msg


def test_infeasibility_diagnostic_analyzer():
    analyzer = InfeasibilityDiagnosticAnalyzer(SolverConfig())
    sections = [{"id": "sec_1", "strength": 100}]
    rooms = [{"id": "r_1", "capacity": 50}]
    
    result = analyzer.analyze_infeasibility(sections, [], rooms, [], {})
    assert result["status"] == "INFEASIBLE_DIAGNOSED"
    assert result["iis_count"] >= 1
    assert result["diagnostics"][0]["constraint_id"] == "HC-05"
