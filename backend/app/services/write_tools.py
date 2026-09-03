"""
Write tools for the autonomous scheduling agent.

Every function here is a mutation path for the timetable. They are kept in one
module so the blast radius of "the agent can change the schedule" is auditable
in a single place.

The invariant all of them share: a write is attempted, the whole timetable is
re-validated with ConflictChecker, and the transaction is rolled back if hard
violations increased. The validator gates the write itself, not just the UI, so
there is no code path that mutates the schedule without passing ground truth.

Before this module existed the agent had 19 read tools and no write tools at
all: approving a repair emitted an audit event reading "Local repair approved
and schedule updated" while leaving every timetable row untouched.
"""

import time
from typing import List, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faculty import Faculty
from app.models.room import Room
from app.models.section import Section
from app.models.subject import Subject
from app.models.time_slot import TimeSlot
from app.models.timetable import TimetableEntry, TimetableVersion
from app.models.timetable_entry_faculty import TimetableEntryFaculty
from app.services.timetable_service import TimetableService
from backend.solver.conflict_checker import ConflictChecker


def normalize_code(value: Any) -> str:
    """Normalise a section/room/subject code for lookup (case, spaces, dashes)."""
    return str(value or "").replace(" ", "").replace("-", "").upper()


async def resolve_lookup_maps(db: AsyncSession) -> Dict[str, Any]:
    """Build code -> id maps for sections, rooms, subjects and time slots."""
    sections = (await db.execute(select(Section))).scalars().all()
    rooms = (await db.execute(select(Room))).scalars().all()
    subjects = (await db.execute(select(Subject))).scalars().all()
    slots = (await db.execute(select(TimeSlot))).scalars().all()

    return {
        "sections": {normalize_code(s.name): s.id for s in sections},
        "rooms": {normalize_code(r.code): r.id for r in rooms},
        "subjects": {normalize_code(s.code): s.id for s in subjects},
        "slots": {
            (str(s.day).upper()[:3], int(s.period)): s.id
            for s in slots
            if s.period is not None
        },
    }


def _slot_key(entry: Dict[str, Any]) -> Optional[tuple]:
    """Extract a (DAY, period) lookup key from a candidate entry dict."""
    day = str(entry.get("day") or "").upper()[:3]
    period = entry.get("period")
    if not day or period is None:
        return None
    try:
        return (day, int(period))
    except (TypeError, ValueError):
        return None


async def apply_timetable_change(
    db: AsyncSession,
    session_id: int,
    entries: List[Dict[str, Any]],
    version_id: int = 5,
    reason: str = "agent_repair",
) -> Dict[str, Any]:
    """
    Persist a candidate schedule onto existing timetable_entries rows.

    This is the single mutation path for agent repairs. Approving a repair
    without calling it means the schedule was never actually updated.
    """
    from app.services.tool_registry import ToolRegistry

    started = time.time()
    if not entries:
        raise ValueError("No entries supplied to apply_timetable_change")

    before = await TimetableService.get_version_timetable(
        db, version_id=version_id, section_name="ALL"
    )
    before_entries = before.get("entries", [])
    before_violations = ConflictChecker().detect(before_entries).total_hard_violations

    # Reject obviously worse candidates before touching any row.
    candidate_violations = ConflictChecker().detect(entries).total_hard_violations
    if candidate_violations > before_violations:
        raise ValueError(
            f"Refusing to apply: hard violations would rise from "
            f"{before_violations} to {candidate_violations}."
        )

    await ToolRegistry.save_schedule_snapshot(
        db, session_id, before_entries, label="pre_apply"
    )

    maps = await resolve_lookup_maps(db)
    updated = 0
    skipped = 0

    for entry in entries:
        entry_id = entry.get("id")
        slot_key = _slot_key(entry)
        if not entry_id or slot_key is None:
            skipped += 1
            continue
        slot_id = maps["slots"].get(slot_key)
        if slot_id is None:
            skipped += 1
            continue

        row = (
            await db.execute(
                select(TimetableEntry)
                .where(TimetableEntry.id == int(entry_id))
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            skipped += 1
            continue

        row.time_slot_id = slot_id
        room_id = maps["rooms"].get(normalize_code(entry.get("room")))
        if room_id is not None:
            row.room_id = room_id
        row.raw_room_text = str(entry.get("room") or "")
        updated += 1

    await db.flush()

    # Re-read through the same path the agent observes with, so the check is
    # against what everyone will actually see, not against our in-memory guess.
    verify = await TimetableService.get_version_timetable(
        db, version_id=version_id, section_name="ALL"
    )
    after_violations = ConflictChecker().detect(verify.get("entries", [])).total_hard_violations

    if after_violations > before_violations:
        await db.rollback()
        raise ValueError(
            f"Applied change rolled back: post-write validation found "
            f"{after_violations} hard violations (was {before_violations})."
        )

    await db.commit()
    await ToolRegistry.log_action(
        db,
        session_id,
        "apply_timetable_change",
        {"version_id": version_id, "reason": reason, "candidate_count": len(entries)},
        {
            "updated": updated,
            "skipped": skipped,
            "hard_violations_after": after_violations,
        },
        int((time.time() - started) * 1000),
    )
    return {
        "status": "applied",
        "updated": updated,
        "skipped": skipped,
        "hard_violations_before": before_violations,
        "hard_violations_after": after_violations,
    }


async def publish_schedule(
    db: AsyncSession,
    session_id: int,
    entries: List[Dict[str, Any]],
    version_label: str,
    source_version_id: int = 5,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Create a new immutable timetable version from a validated candidate.

    Refused unless the candidate has zero hard violations, so any published
    version is clean by construction.
    """
    from app.services.tool_registry import ToolRegistry

    started = time.time()
    report = ConflictChecker().detect(entries)
    if report.total_hard_violations > 0:
        raise ValueError(
            f"Refusing to publish {version_label}: {report.total_hard_violations} "
            f"hard violation(s) ({report.physical_room_clashes} room, "
            f"{report.faculty_clashes} faculty, {report.student_clashes} section)."
        )

    existing = (
        await db.execute(
            select(TimetableVersion).where(
                TimetableVersion.version_label == version_label
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError(f"Version label {version_label} already exists")

    source = (
        await db.execute(
            select(TimetableVersion).where(TimetableVersion.id == source_version_id)
        )
    ).scalar_one_or_none()

    new_version = TimetableVersion(
        academic_year_id=getattr(source, "academic_year_id", None) or 1,
        version_label=version_label,
        is_current=False,
        source="agent",
        notes=notes or f"Published by agent session {session_id}",
    )
    db.add(new_version)
    await db.flush()

    maps = await resolve_lookup_maps(db)
    written = 0
    unresolved = 0

    for entry in entries:
        section_id = maps["sections"].get(normalize_code(entry.get("section")))
        slot_key = _slot_key(entry)
        slot_id = maps["slots"].get(slot_key) if slot_key else None
        if section_id is None or slot_id is None:
            unresolved += 1
            continue

        db.add(
            TimetableEntry(
                timetable_version_id=new_version.id,
                section_id=section_id,
                subject_id=maps["subjects"].get(normalize_code(entry.get("subject"))),
                room_id=maps["rooms"].get(normalize_code(entry.get("room"))),
                time_slot_id=slot_id,
                faculty_ids=list(entry.get("faculty_ids") or []),
                entry_type=str(entry.get("entry_type") or "L"),
                span_periods=int(entry.get("span_periods") or 1),
                raw_subject_text=str(entry.get("subject") or ""),
                raw_room_text=str(entry.get("room") or ""),
            )
        )
        written += 1

    await db.commit()
    await ToolRegistry.log_action(
        db,
        session_id,
        "publish_schedule",
        {"version_label": version_label, "candidate_count": len(entries)},
        {"version_id": new_version.id, "written": written, "unresolved": unresolved},
        int((time.time() - started) * 1000),
    )
    return {
        "status": "published",
        "version_id": new_version.id,
        "version_label": version_label,
        "entries_written": written,
        "unresolved": unresolved,
        "hard_violations": 0,
    }


async def assign_faculty_to_entry(
    db: AsyncSession,
    session_id: int,
    entry_id: int,
    faculty_ids: List[int],
) -> Dict[str, Any]:
    """
    Assign instructors to one timetable entry.

    Rejected if it would double-book any of them. Keeps faculty_ids and the
    timetable_entry_faculty join table in step, since the read path prefers the
    join table and silently falls back to the JSON column.
    """
    from app.services.tool_registry import ToolRegistry

    started = time.time()
    if not faculty_ids:
        raise ValueError("No faculty_ids supplied")

    row = (
        await db.execute(
            select(TimetableEntry)
            .where(TimetableEntry.id == int(entry_id))
            .with_for_update()
        )
    ).scalar_one_or_none()
    if row is None:
        raise ValueError(f"Timetable entry {entry_id} not found")

    faculty_rows = (
        await db.execute(select(Faculty).where(Faculty.id.in_(faculty_ids)))
    ).scalars().all()
    if len(faculty_rows) != len(set(faculty_ids)):
        missing = sorted(set(faculty_ids) - {f.id for f in faculty_rows})
        raise ValueError(f"Unknown faculty id(s): {missing}")

    names_by_id = {f.id: f.name for f in faculty_rows}
    ordered_names = [names_by_id[fid] for fid in faculty_ids]

    current = await TimetableService.get_version_timetable(
        db, version_id=row.timetable_version_id, section_name="ALL"
    )
    baseline_entries = current.get("entries", [])
    baseline_clashes = ConflictChecker().detect(baseline_entries).faculty_clashes

    proposed = []
    for candidate in baseline_entries:
        candidate = dict(candidate)
        if candidate.get("id") == row.id:
            candidate["faculty"] = ordered_names
        proposed.append(candidate)

    proposed_clashes = ConflictChecker().detect(proposed).faculty_clashes
    if proposed_clashes > baseline_clashes:
        raise ValueError(
            f"Refusing assignment: it would create "
            f"{proposed_clashes - baseline_clashes} faculty double-booking(s)."
        )

    row.faculty_ids = list(faculty_ids)
    await db.execute(
        TimetableEntryFaculty.__table__.delete().where(
            TimetableEntryFaculty.timetable_entry_id == row.id
        )
    )
    for index, faculty_id in enumerate(faculty_ids):
        db.add(
            TimetableEntryFaculty(
                timetable_entry_id=row.id,
                faculty_id=faculty_id,
                role_type="LEAD" if index == 0 else "CO_INSTRUCTOR",
            )
        )

    await db.commit()
    await ToolRegistry.log_action(
        db,
        session_id,
        "assign_faculty_to_entry",
        {"entry_id": entry_id, "faculty_ids": faculty_ids},
        {"assigned": len(faculty_ids), "faculty": ordered_names},
        int((time.time() - started) * 1000),
    )
    return {"status": "assigned", "entry_id": row.id, "faculty": ordered_names}


async def create_timetable_entry(
    db: AsyncSession,
    session_id: int,
    section: str,
    subject: str,
    day: str,
    period: int,
    room: str,
    entry_type: str = "L",
    faculty_ids: Optional[List[int]] = None,
    version_id: int = 5,
) -> Dict[str, Any]:
    """Create a brand new class slot, refusing any placement that clashes."""
    from app.services.tool_registry import ToolRegistry

    started = time.time()
    maps = await resolve_lookup_maps(db)

    section_id = maps["sections"].get(normalize_code(section))
    if section_id is None:
        raise ValueError(f"Unknown section: {section}")

    slot_id = maps["slots"].get((str(day).upper()[:3], int(period)))
    if slot_id is None:
        raise ValueError(f"Unknown time slot: {day} P{period}")

    room_id = maps["rooms"].get(normalize_code(room))
    if room_id is None:
        raise ValueError(f"Unknown room: {room}")

    faculty_ids = list(faculty_ids or [])
    faculty_names: List[str] = []
    if faculty_ids:
        faculty_rows = (
            await db.execute(select(Faculty).where(Faculty.id.in_(faculty_ids)))
        ).scalars().all()
        if len(faculty_rows) != len(set(faculty_ids)):
            missing = sorted(set(faculty_ids) - {f.id for f in faculty_rows})
            raise ValueError(f"Unknown faculty id(s): {missing}")
        names_by_id = {f.id: f.name for f in faculty_rows}
        faculty_names = [names_by_id[fid] for fid in faculty_ids]

    current = await TimetableService.get_version_timetable(
        db, version_id=version_id, section_name="ALL"
    )
    baseline_entries = current.get("entries", [])
    baseline_violations = ConflictChecker().detect(baseline_entries).total_hard_violations

    proposed = list(baseline_entries) + [
        {
            "id": -1,
            "section": section,
            "day": str(day).upper()[:3],
            "period": int(period),
            "subject": subject,
            "room": room,
            "faculty": faculty_names,
            "entry_type": entry_type,
            "span_periods": 1,
        }
    ]
    proposed_violations = ConflictChecker().detect(proposed).total_hard_violations
    if proposed_violations > baseline_violations:
        raise ValueError(
            f"Refusing to create entry: placement raises hard violations from "
            f"{baseline_violations} to {proposed_violations}."
        )

    row = TimetableEntry(
        timetable_version_id=version_id,
        section_id=section_id,
        subject_id=maps["subjects"].get(normalize_code(subject)),
        room_id=room_id,
        time_slot_id=slot_id,
        faculty_ids=faculty_ids,
        entry_type=entry_type,
        span_periods=1,
        raw_subject_text=subject,
        raw_room_text=room,
    )
    db.add(row)
    await db.flush()

    for index, faculty_id in enumerate(faculty_ids):
        db.add(
            TimetableEntryFaculty(
                timetable_entry_id=row.id,
                faculty_id=faculty_id,
                role_type="LEAD" if index == 0 else "CO_INSTRUCTOR",
            )
        )

    await db.commit()
    await db.refresh(row)
    await ToolRegistry.log_action(
        db,
        session_id,
        "create_timetable_entry",
        {
            "section": section,
            "subject": subject,
            "day": day,
            "period": period,
            "room": room,
        },
        {"entry_id": row.id},
        int((time.time() - started) * 1000),
    )
    return {
        "status": "created",
        "entry_id": row.id,
        "section": section,
        "subject": subject,
        "day": day,
        "period": period,
        "room": room,
        "faculty": faculty_names,
    }
