import pytest
import datetime
from sqlalchemy import select
from app.services.write_tools import apply_timetable_change, publish_schedule, delete_timetable_entry
from app.services.tool_registry import ToolRegistry
from app.services.substitute_dispatcher import SubstituteDispatcher
from app.models.section import Section
from app.models.room import Room
from app.models.subject import Subject
from app.models.time_slot import TimeSlot
from app.models.faculty import Faculty
from app.models.timetable import TimetableVersion, TimetableEntry
from app.models.timetable_entry_faculty import TimetableEntryFaculty
from app.models.agent import AgentSession


@pytest.mark.asyncio
async def test_apply_timetable_change_faculty_persistence(async_db_session):
    sec = Section(name="II AIML A", label="A", branch_id=1, academic_year_id=1, year_level=2)
    rm = Room(code="601", capacity=60, room_type="classroom")
    subj = Subject(code="DS", full_name="Data Structures", slot_type="L")
    slot = TimeSlot(day="MON", period=1, start_time=datetime.time(8, 15), end_time=datetime.time(9, 5))
    f1 = Faculty(name="Dr. S. Srikantha Reddy", designation="Professor", max_hours_per_week=12)
    f2 = Faculty(name="Dr. P. Kalpana", designation="Associate Professor", max_hours_per_week=14)
    ver = TimetableVersion(academic_year_id=1, version_label="TEST-V5", is_current=True)

    async_db_session.add_all([sec, rm, subj, slot, f1, f2, ver])
    await async_db_session.flush()

    entry = TimetableEntry(
        timetable_version_id=ver.id,
        section_id=sec.id,
        subject_id=subj.id,
        room_id=rm.id,
        time_slot_id=slot.id,
        faculty_ids=[f1.id],
        entry_type="L",
        raw_room_text="601",
        raw_subject_text="DS",
    )
    async_db_session.add(entry)
    await async_db_session.flush()

    async_db_session.add(TimetableEntryFaculty(
        timetable_entry_id=entry.id,
        faculty_id=f1.id,
        role_type="LEAD"
    ))

    sess = AgentSession(goal="Test Faculty Persistence", status="active")
    async_db_session.add(sess)
    await async_db_session.commit()

    candidate = [{
        "id": entry.id,
        "section": "II AIML A",
        "day": "MON",
        "period": 1,
        "room": "601",
        "subject": "DS",
        "faculty_ids": [f1.id, f2.id],
        "entry_type": "L",
    }]

    result = await ToolRegistry.apply_timetable_change(
        async_db_session,
        session_id=sess.id,
        entries=candidate,
        version_id=ver.id,
        reason="test_faculty_sync"
    )
    assert result["status"] == "applied"

    # Verify TimetableEntry and TimetableEntryFaculty rows in DB
    updated_entry = (await async_db_session.execute(
        select(TimetableEntry).where(TimetableEntry.id == entry.id)
    )).scalar_one()
    assert updated_entry.faculty_ids == [f1.id, f2.id]

    join_rows = (await async_db_session.execute(
        select(TimetableEntryFaculty).where(TimetableEntryFaculty.timetable_entry_id == entry.id)
    )).scalars().all()
    assert len(join_rows) == 2
    fids = [j.faculty_id for j in join_rows]
    assert f1.id in fids and f2.id in fids


@pytest.mark.asyncio
async def test_publish_schedule_and_delete_entry(async_db_session):
    sec = Section(name="II AIML B", label="B", branch_id=1, academic_year_id=1, year_level=2)
    rm = Room(code="602", capacity=60, room_type="classroom")
    subj = Subject(code="AI", full_name="Artificial Intelligence", slot_type="L")
    slot = TimeSlot(day="TUE", period=2, start_time=datetime.time(9, 5), end_time=datetime.time(9, 55))
    f = Faculty(name="Dr. K. Srinivas", designation="Assistant Professor", max_hours_per_week=16)
    src_ver = TimetableVersion(academic_year_id=1, version_label="SRC-V1", is_current=False)

    async_db_session.add_all([sec, rm, subj, slot, f, src_ver])
    await async_db_session.flush()

    sess = AgentSession(goal="Test Publish & Delete", status="active")
    async_db_session.add(sess)
    await async_db_session.commit()

    candidate = [{
        "section": "II AIML B",
        "day": "TUE",
        "period": 2,
        "room": "602",
        "subject": "AI",
        "faculty_ids": [f.id],
        "entry_type": "L",
    }]

    published = await ToolRegistry.publish_schedule(
        async_db_session,
        session_id=sess.id,
        entries=candidate,
        version_label="TEST-PUBLISH-CLEAN",
        source_version_id=src_ver.id
    )
    assert published["status"] == "published"
    assert published["entries_written"] == 1
    new_version_id = published["version_id"]

    new_entries = (await async_db_session.execute(
        select(TimetableEntry).where(TimetableEntry.timetable_version_id == new_version_id)
    )).scalars().all()
    assert len(new_entries) == 1
    published_entry_id = new_entries[0].id

    # Verify TimetableEntryFaculty row was created
    entry_facs = (await async_db_session.execute(
        select(TimetableEntryFaculty).where(TimetableEntryFaculty.timetable_entry_id == published_entry_id)
    )).scalars().all()
    assert len(entry_facs) == 1
    assert entry_facs[0].faculty_id == f.id

    # Test delete_timetable_entry tool
    del_res = await ToolRegistry.delete_timetable_entry(
        async_db_session,
        session_id=sess.id,
        entry_id=published_entry_id,
        reason="test_cancellation"
    )
    assert del_res["status"] == "deleted"

    # Verify deleted row does not exist
    deleted_check = (await async_db_session.execute(
        select(TimetableEntry).where(TimetableEntry.id == published_entry_id)
    )).scalar_one_or_none()
    assert deleted_check is None


@pytest.mark.asyncio
async def test_substitute_dispatcher_with_impacted_slot(async_db_session):
    result = await SubstituteDispatcher.find_candidate_substitutes(
        db=async_db_session,
        faculty_name="Dr. S. Srikantha Reddy",
        day="MON",
        period=1,
        subject_code="DS",
        version_id=5
    )
    assert "candidates" in result
    assert result["absent_faculty"] == "Dr. S. Srikantha Reddy"
    # Verify candidate response contains impacted_slot field
    assert "impacted_slot" in result
