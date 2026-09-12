import pytest
from app.services.calendar_sync_service import CalendarSyncService


@pytest.mark.asyncio
async def test_generate_section_ical(async_db_session):
    ics_text = await CalendarSyncService.generate_section_ical(
        db=async_db_session,
        section_identifier="II AIML-A",
        version_id=5
    )
    assert "BEGIN:VCALENDAR" in ics_text
    assert "VERSION:2.0" in ics_text
    assert "END:VCALENDAR" in ics_text
    assert "BEGIN:VEVENT" in ics_text
    assert "RRULE:FREQ=WEEKLY" in ics_text


@pytest.mark.asyncio
async def test_generate_cohort_ical(async_db_session):
    ics_text = await CalendarSyncService.generate_cohort_ical(
        db=async_db_session,
        cohort_key="YEAR_2",
        version_id=5
    )
    assert "BEGIN:VCALENDAR" in ics_text
    assert "VFSTR 2nd Year Cohort Master Calendar" in ics_text
    assert "END:VCALENDAR" in ics_text


@pytest.mark.asyncio
async def test_generate_master_ical(async_db_session):
    ics_text = await CalendarSyncService.generate_master_ical(
        db=async_db_session,
        version_id=5
    )
    assert "BEGIN:VCALENDAR" in ics_text
    assert "VFSTR ACSE Master Timetable V5" in ics_text
    assert "END:VCALENDAR" in ics_text

