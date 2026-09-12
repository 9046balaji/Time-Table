import pytest
from app.services.exam_scheduler_agent import ExamSchedulerAgent


@pytest.mark.asyncio
async def test_generate_exam_schedule(async_db_session):
    result = await ExamSchedulerAgent.generate_exam_schedule(
        db=async_db_session,
        exam_type="MID_TERM_1",
        start_date="2026-10-12",
        num_days=4,
        spacing_factor=0.5,
        target_sections=["II AIML-A", "II AIML-B", "III AIML-A"]
    )
    assert result["status"] == "COMPLETED"
    assert result["total_exams_scheduled"] > 0
    assert result["hard_violations"] == 0
    assert len(result["scheduled_exams"]) > 0

    first_exam = result["scheduled_exams"][0]
    assert "section" in first_exam
    assert "subject" in first_exam
    assert "date" in first_exam
    assert "session" in first_exam
    assert len(first_exam["allocated_rooms"]) > 0
    assert len(first_exam["invigilators"]) > 0


def test_audit_exam_timetable_detects_clashes():
    # Test valid
    valid_exams = [
        {"section": "II AIML-A", "subject": "DS", "date": "2026-10-12", "session": "MORNING", "allocated_rooms": ["601"], "invigilators": ["Dr. A"]},
        {"section": "II AIML-A", "subject": "AI", "date": "2026-10-13", "session": "MORNING", "allocated_rooms": ["601"], "invigilators": ["Dr. B"]},
    ]
    report = ExamSchedulerAgent.audit_exam_timetable(valid_exams)
    assert report["is_valid"] is True
    assert report["hard_violations"] == 0

    # Test student clash (same day multiple exams)
    clash_exams = [
        {"section": "II AIML-A", "subject": "DS", "date": "2026-10-12", "session": "MORNING", "allocated_rooms": ["601"], "invigilators": ["Dr. A"]},
        {"section": "II AIML-A", "subject": "AI", "date": "2026-10-12", "session": "AFTERNOON", "allocated_rooms": ["602"], "invigilators": ["Dr. B"]},
    ]
    clash_report = ExamSchedulerAgent.audit_exam_timetable(clash_exams)
    assert clash_report["is_valid"] is False
    assert clash_report["student_clashes"] == 1
