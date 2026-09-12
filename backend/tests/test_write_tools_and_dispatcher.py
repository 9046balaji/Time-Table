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


@pytest.mark.asyncio
async def test_master_arbiter_session_persistence(async_db_session):
    from app.services.multi_agent_scheduler import MasterArbiterAgent
    from app.models.agent import AgentEvent, AgentDecision

    sess = AgentSession(goal="Test Collaborative Multi-Agent Synthesis", status="active")
    async_db_session.add(sess)
    await async_db_session.commit()

    arbiter = MasterArbiterAgent(db=async_db_session, session_id=sess.id)
    synth_res = await arbiter.execute_collaborative_synthesis(
        target_version_id=5,
        max_negotiation_rounds=1,
        scope="ALL"
    )
    assert "votes" in synth_res
    assert len(synth_res["votes"]) == 7

    # Verify session was updated with candidate entries and consensus step
    updated_sess = (await async_db_session.execute(
        select(AgentSession).where(AgentSession.id == sess.id)
    )).scalar_one()
    assert updated_sess.current_step == "consensus"
    assert "candidate_entries" in updated_sess.context
    assert len(updated_sess.context["candidate_entries"]) > 0

    # Verify AgentEvent was created
    ev = (await async_db_session.execute(
        select(AgentEvent).where(
            AgentEvent.session_id == sess.id,
            AgentEvent.event_type == "MULTI_AGENT_SYNTHESIS_COMPLETE"
        )
    )).scalar_one_or_none()
    assert ev is not None


@pytest.mark.asyncio
async def test_exam_scheduler_with_session_id(async_db_session):
    from app.services.exam_scheduler_agent import ExamSchedulerAgent
    from app.models.agent import AgentEvent, AgentDecision

    sess = AgentSession(goal="Test Exam Schedule Generation", status="active")
    async_db_session.add(sess)
    await async_db_session.commit()

    exam_res = await ExamSchedulerAgent.generate_exam_schedule(
        db=async_db_session,
        exam_type="MID_TERM_1",
        num_days=4,
        session_id=sess.id
    )
    assert exam_res["status"] in ("COMPLETED", "WARNING")
    assert exam_res["total_exams_scheduled"] > 0

    # Verify session context updated
    updated_sess = (await async_db_session.execute(
        select(AgentSession).where(AgentSession.id == sess.id)
    )).scalar_one()
    assert "exam_schedule" in updated_sess.context
    assert updated_sess.context["exam_schedule"]["total_exams"] == exam_res["total_exams_scheduled"]

    # Verify AgentEvent and AgentDecision
    ev = (await async_db_session.execute(
        select(AgentEvent).where(
            AgentEvent.session_id == sess.id,
            AgentEvent.event_type == "EXAM_SCHEDULE_GENERATED"
        )
    )).scalar_one_or_none()
    assert ev is not None

    dec = (await async_db_session.execute(
        select(AgentDecision).where(
            AgentDecision.session_id == sess.id,
            AgentDecision.decision_type == "EXAM_SCHEDULE_OPTIMIZED"
        )
    )).scalar_one_or_none()
    assert dec is not None


@pytest.mark.asyncio
async def test_multi_agent_consensus_session_state(async_db_session):
    from app.services.multi_agent_consensus import MultiAgentConsensusEngine

    sess = AgentSession(goal="Test Consensus Session State", status="active")
    async_db_session.add(sess)
    await async_db_session.commit()

    # Fetch baseline entries to evaluate
    tt_data = await ToolRegistry.get_current_timetable(async_db_session)
    entries = tt_data.get("entries", [])

    consensus_res = await MultiAgentConsensusEngine.evaluate_consensus(
        db=async_db_session,
        session_id=sess.id,
        timetable_entries=entries[:20]
    )
    assert "consensus_passed" in consensus_res

    updated_sess = (await async_db_session.execute(
        select(AgentSession).where(AgentSession.id == sess.id)
    )).scalar_one()
    assert updated_sess.current_step in ("publish", "repair")
    assert "last_consensus" in updated_sess.context

