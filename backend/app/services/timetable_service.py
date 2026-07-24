from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.timetable import TimetableVersion, TimetableEntry
from app.models.section import Section
from app.models.room import Room
from app.models.time_slot import TimeSlot
from app.models.faculty import Faculty


class TimetableService:
    @staticmethod
    async def get_version_timetable(
        db: Optional[AsyncSession],
        version_id: int = 5,
        section_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch timetable entries from DB asynchronously for a given version."""
        result = []
        if db is not None:
            try:
                stmt = select(TimetableEntry, Section, TimeSlot, Room)\
                    .outerjoin(Section, TimetableEntry.section_id == Section.id)\
                    .outerjoin(TimeSlot, TimetableEntry.time_slot_id == TimeSlot.id)\
                    .outerjoin(Room, TimetableEntry.room_id == Room.id)\
                    .where(TimetableEntry.timetable_version_id == version_id)

                if section_name:
                    stmt = stmt.where(Section.name == section_name)

                res = await db.execute(stmt)
                rows = res.all()
                for e, sec, ts, rm in rows:
                    sec_name = sec.name if sec else "II AIML-A"
                    day_val = ts.day if ts else "MON"
                    period_val = ts.period if ts else 1
                    room_val = rm.code if rm else (e.raw_room_text or "")
                    
                    result.append({
                        "id": e.id,
                        "section": sec_name,
                        "day": day_val,
                        "period": period_val,
                        "subject": e.raw_subject_text or "DS",
                        "room": room_val,
                        "faculty": e.raw_faculty_text.split(", ") if e.raw_faculty_text else [],
                        "entry_type": e.entry_type or "L",
                        "span_periods": e.span_periods or 1
                    })
            except Exception as ex:
                print(f"[TimetableService Error] {ex}")

        return {
            "version_id": version_id,
            "count": len(result),
            "entries": result
        }

    @staticmethod
    async def get_faculty_timetable(
        db: Optional[AsyncSession],
        faculty_id: Optional[int] = None,
        faculty_name: Optional[str] = None,
        version_id: int = 5
    ) -> Dict[str, Any]:
        """Fetch weekly teaching schedule specifically for a single faculty member."""
        result = []
        target_name = faculty_name or ""
        fac_obj = None

        if db is not None:
            try:
                if faculty_id:
                    fac_res = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
                    fac_obj = fac_res.scalar_one_or_none()
                    if fac_obj:
                        target_name = fac_obj.name

                stmt = select(TimetableEntry, Section, TimeSlot, Room)\
                    .outerjoin(Section, TimetableEntry.section_id == Section.id)\
                    .outerjoin(TimeSlot, TimetableEntry.time_slot_id == TimeSlot.id)\
                    .outerjoin(Room, TimetableEntry.room_id == Room.id)\
                    .where(TimetableEntry.timetable_version_id == version_id)

                res = await db.execute(stmt)
                rows = res.all()
                for e, sec, ts, rm in rows:
                    raw_fac = e.raw_faculty_text or ""
                    # Check if faculty ID or faculty name matches entry
                    is_match = (faculty_id and e.faculty_ids and faculty_id in e.faculty_ids) or \
                               (target_name and target_name.lower() in raw_fac.lower())
                    if is_match:
                        result.append({
                            "id": e.id,
                            "section": sec.name if sec else "II AIML-A",
                            "day": ts.day if ts else "MON",
                            "period": ts.period if ts else 1,
                            "subject": e.raw_subject_text or "",
                            "room": rm.code if rm else (e.raw_room_text or ""),
                            "faculty": raw_fac.split(", "),
                            "entry_type": e.entry_type or "L"
                        })
            except Exception as ex:
                print(f"[FacultyTimetable Error] {ex}")

        max_hours = fac_obj.max_hours_per_week if fac_obj else 16
        assigned_hours = len(result)

        return {
            "faculty_id": faculty_id,
            "faculty_name": target_name or "Faculty Member",
            "designation": fac_obj.designation if fac_obj else "Assistant Professor",
            "max_hours_per_week": max_hours,
            "assigned_hours": assigned_hours,
            "count": len(result),
            "entries": result
        }

    @staticmethod
    async def update_entry_slot(
        db: AsyncSession,
        entry_id: int,
        new_time_slot_id: int,
        new_room_id: Optional[int] = None
    ) -> Optional[TimetableEntry]:
        """Update a specific entry slot assignment asynchronously."""
        stmt = select(TimetableEntry).where(TimetableEntry.id == entry_id)
        res = await db.execute(stmt)
        entry = res.scalar_one_or_none()
        if not entry:
            return None

        entry.time_slot_id = new_time_slot_id
        if new_room_id:
            entry.room_id = new_room_id

        await db.commit()
        await db.refresh(entry)
        return entry
